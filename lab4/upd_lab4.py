import datetime
import io
import jwt
import numpy as np
import uvicorn
from PIL import Image
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Response, WebSocket, WebSocketDisconnect
from fastapi import Header
from numpy.lib.stride_tricks import sliding_window_view
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import redis
from celery import Celery

SECRET_KEY = "x25&gd8#f6y1*@!#2p3w9l$r8-6n0a^#4dj01f%" #ключ для создания и проверки JWT-токенов
ALGORITHM = "HS256" #для шифрования
DATABASE_URL = "sqlite:///./test.db"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) #позволяет нескольким потокам приложения использовать одно и то же подключение
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base() #базовый класс для всех моделей бд

app = FastAPI()

redis_client = redis.Redis(host='localhost', port=6379, db=0)
celery_app = Celery("tasks", broker="redis://localhost:6379/0") #хранит задачи, пока не будут выполнены

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

Base.metadata.create_all(bind=engine)

class User(BaseModel):
    id: int
    email: EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class ImageRequest(BaseModel):
    image: str
    algorithm: str = "feny_tan"

def adaptive_threshold_feny_tan(gray_np: np.ndarray, win_size: int = 15, k: float = 0.5,
                                epsilon: float = 1e-8) -> np.ndarray:
    """
    Алгоритм адаптивной бинаризации Феня и Тана предназначен для обработки изображений неоднородной
    освещённости. В отличие от глобальной бинаризации, он учитывает локальный контекст каждого пикселя.
    """
    # добавляем пиксели вокруг фотки, тк нам нужно обработать каждый пиксель
    pad = win_size // 2
    padded = np.pad(gray_np, pad, mode='reflect') #границы изображения дополняются зеркальным отражением

    # создаем локальные области ((H - win_size + 1, W - win_size + 1, win_size, win_size))
    windows = sliding_window_view(padded, (win_size, win_size))

    # среднее и стандартное отклонение по окну
    local_mean = windows.mean(axis=(-1, -2))
    local_std = windows.std(axis=(-1, -2))

    #порог T по формуле алгоритма Феня и Тана
    T = local_mean * (1 + k * ((local_std / (local_mean + epsilon)) - 1))

    # если интенсивность пикселя > T, то белый, иначе чёрный
    binary = (gray_np > T).astype(np.uint8) * 255
    return binary

# JWT токены  
def create_token(user_id: int):
    payload = {"user_id": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Header(...), db: Session = Depends(get_db)):
    try:
        if token.startswith("Bearer "):
            token = token.split("Bearer ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["user_id"]
        user = db.query(UserDB).filter(UserDB.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="Пользователь не найден")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Недействительный токен")

# CRUD'ы
@app.post("/sign-up/")
def sign_up(user_data: UserCreate, db: Session = Depends(get_db)):
    user_exists = db.query(UserDB).filter(UserDB.email == user_data.email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Такой email уже есть")

    hashed_password = pwd_context.hash(user_data.password)
    new_user = UserDB(email=user_data.email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_token(new_user.id)
    return {"id": new_user.id, "email": new_user.email, "token": token}

@app.post("/login/")
def login(user_data: UserCreate, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == user_data.email).first()
    if not user or not pwd_context.verify(user_data.password, user.password):
        raise HTTPException(status_code=400, detail="Неверные учетные данные")

    token = create_token(user.id)
    return {"id": user.id, "email": user.email, "token": token}

@app.get("/users/me/")
def get_me(user: UserDB = Depends(get_current_user)):
    return {"id": user.id, "email": user.email}

# Эндпоинт бинаризации изображения
@app.post("/binary_image")
async def binary_image_endpoint(
    file: UploadFile = File(...),
    user: UserDB = Depends(get_current_user)
):
    if not file.filename.lower().endswith(".png"):
        return Response(content="Только PNG-файлы поддерживаются!", status_code=400)

    image = Image.open(file.file).convert("L")
    gray_np = np.array(image, dtype=np.float32)
    binary_np = adaptive_threshold_feny_tan(gray_np)

    binary_image = Image.fromarray(binary_np)

    img_io = io.BytesIO()
    binary_image.save(img_io, format="PNG")
    img_io.seek(0)

    return Response(content=img_io.getvalue(), media_type="image/png")

@app.get("/users/", response_model=list[User])
def read_users(db: Session = Depends(get_db)):
    return db.query(UserDB).all()

#обновление пользователя
@app.put("/users/{user_id}/", response_model=User)
def update_user(user_id: int, user_data: UserCreate, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user.email = user_data.email
    user.password = pwd_context.hash(user_data.password)
    db.commit()
    db.refresh(user)
    return user

@app.delete("/users/{user_id}/")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    db.delete(user)
    db.commit()
    return {"detail": "Пользователь удалён"}

# WebSocket
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        pass
#https://piehost.com/websocket-tester


#Celery
@celery_app.task
def example_async_task(data):
    redis_client.set('async_data', data)

if __name__ == "__main__":
    uvicorn.run("upd_lab3:app", host="0.0.0.0", port=8000, reload=True)

#http://127.0.0.1:8000/docs