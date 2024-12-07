import logging
import random
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow, QInputDialog, QDialog, QVBoxLayout, QFormLayout, QLineEdit, QLabel, QStatusBar, \
    QAction, QToolBar, QWidget, QHBoxLayout, QPushButton
from PyQt5.QtGui import QPainter, QColor, QBrush
from PyQt5.QtCore import QTimer
import json
import os
import logging
import math
import random


class MainWindow(QMainWindow):
    def __init__(self, farm):
        super().__init__()
        self.farm = farm
        self.setWindowTitle("Огород с капустой и овцами")
        self.setGeometry(100, 100, self.farm.width + 200, self.farm.height)  # Добавляем место для боковой панели

        # Центральный виджет
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Таймер обновления
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_farm)
        self.timer.start(50)

        # Создаем меню
        self.create_menu()

        # Создаем панель инструментов
        self.create_toolbar()

        # Создаем статусную строку
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Боковая панель информации
        self.info_panel = QWidget()
        self.info_layout = QVBoxLayout()
        self.info_panel.setLayout(self.info_layout)

        self.goat_count_label = QLabel("Количество овец: 0")
        self.cabbage_count_label = QLabel("Количество капусты: 0")
        self.info_layout.addWidget(self.goat_count_label)
        self.info_layout.addWidget(self.cabbage_count_label)

        # Основной макет
        self.main_layout = QHBoxLayout()
        self.main_layout.addWidget(self.info_panel)
        self.main_layout.addStretch()
        self.central_widget.setLayout(self.main_layout)

    def create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")
        help_menu = menubar.addMenu("Помощь")

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        toolbar = QToolBar("Инструменты")
        self.addToolBar(toolbar)

        add_herd_action = QAction("Добавить стадо", self)
        add_herd_action.triggered.connect(self.open_add_herd_dialog)
        toolbar.addAction(add_herd_action)

    def update_farm(self):
        self.farm.update(self.status_bar)
        self.update()
        self.update_info_panel()

    def update_info_panel(self):
        total_goats = sum(len(herd.goats) for herd in self.farm.herds)
        total_cabbages = len(self.farm.cabbages)
        self.goat_count_label.setText(f"Количество овец: {total_goats}")
        self.cabbage_count_label.setText(f"Количество капусты: {total_cabbages}")

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.translate(200, 0)  # Сдвигаем поле вправо для боковой панели
            painter.setBrush(QColor(0, 255, 0))
            for cabbage in self.farm.cabbages:
                painter.drawEllipse(int(cabbage.x), int(cabbage.y), int(cabbage.size), int(cabbage.size))

            for herd in self.farm.herds:
                for goat in herd.goats:
                    # Цвет козы зависит от уровня голода
                    hunger_ratio = goat.hunger / goat.max_hunger
                    color_intensity = int(255 * (1 - hunger_ratio))
                    painter.setBrush(QColor(255, color_intensity, color_intensity))
                    painter.drawEllipse(int(goat.x), int(goat.y), 5, 5)

                painter.setBrush(QBrush())
                painter.setPen(QColor(0, 0, 0))
                center_x, center_y, radius = herd.get_center_and_radius()
                painter.drawEllipse(int(center_x - radius), int(center_y - radius), int(radius * 2), int(radius * 2))
        except Exception as e:
            logging.error(f"Ошибка в paintEvent: {e}", exc_info=True)

    def mousePressEvent(self, event):
        if event.x() < 200:
            return  # Игнорируем клики по боковой панели
        x, y = event.x() - 200, event.y()
        volume, ok = QInputDialog.getInt(self, "Создание капусты", "Введите объём капусты:", 20, 10, 100, 1)
        if ok:
            self.farm.cabbages.append(Cabbage(x, y, volume))
            self.update()

    def open_add_herd_dialog(self):
        dialog = AddHerdDialog(self.farm, self)
        if dialog.exec_():
            self.update()

    def show_about_dialog(self):
        QInputDialog.getText(self, "О программе", "Симуляция огорода с капустой и овцами.")

class AddHerdDialog(QDialog):
    def __init__(self, farm, parent=None):
        super().__init__(parent)
        self.farm = farm
        self.setWindowTitle("Добавление нового стада")
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.count_input = QLineEdit("10")
        self.speed_input = QLineEdit("5")
        self.max_hunger_input = QLineEdit("50")
        self.eating_rate_input = QLineEdit("5")
        self.fertility_input = QLineEdit("0.3")

        self.form_layout.addRow("Количество овец:", self.count_input)
        self.form_layout.addRow("Скорость передвижения:", self.speed_input)
        self.form_layout.addRow("Максимальный уровень голода:", self.max_hunger_input)
        self.form_layout.addRow("Скорость поедания капусты:", self.eating_rate_input)
        self.form_layout.addRow("Вероятность размножения:", self.fertility_input)
        self.layout.addLayout(self.form_layout)

        self.add_button = QPushButton("Добавить стадо")
        self.add_button.clicked.connect(self.add_herd)
        self.layout.addWidget(self.add_button)

        self.setLayout(self.layout)

    def add_herd(self):
        try:
            # Чтение параметров
            count = int(self.count_input.text())
            speed = float(self.speed_input.text())
            max_hunger = float(self.max_hunger_input.text())
            eating_rate = float(self.eating_rate_input.text())
            fertility = float(self.fertility_input.text())

            if count <= 0:
                raise ValueError("Количество овец должно быть больше 0")
            if speed <= 0 or max_hunger <= 0 or eating_rate <= 0 or fertility <= 0:
                raise ValueError("Все параметры должны быть положительными")

            logging.debug(f"Попытка добавить стадо: количество={count}, скорость={speed}, "
                          f"макс. голод={max_hunger}, скорость поедания={eating_rate}, плодовитость={fertility}")

            # Создание нового стада
            max_offset = 5
            base_x = random.randint(max_offset, self.farm.width - max_offset)
            base_y = random.randint(max_offset, self.farm.height - max_offset)
            goats = [
                Goat(
                    x=base_x + random.uniform(-max_offset, max_offset),
                    y=base_y + random.uniform(-max_offset, max_offset),
                    speed=speed,
                    max_hunger=max_hunger,
                    eating_rate=eating_rate,
                    fertility=fertility
                )
                for _ in range(count)
            ]
            self.farm.add_herd(Herd(goats))
            logging.debug(f"Стадо успешно добавлено: центр стада x={base_x}, y={base_y}, количество овец={count}")
            self.accept()
        except ValueError as ve:
            logging.error(f"Ошибка при вводе параметров: {ve}", exc_info=True)
        except Exception:
            logging.error("Ошибка при добавлении нового стада", exc_info=True)

DEFAULT_DATA = {
    "goats": {
        "speed": 5.0,
        "max_hunger": 50,
        "eating_rate": 5.0,
        "fertility": 0.3,
        "count": 10
    },
    "cabbages": [],
    "farm_size": {"width": 800, "height": 600}
}

def load_initial_data(filename="config.json"):
    if not os.path.exists(filename):
        with open(filename, "w") as file:
            json.dump(DEFAULT_DATA, file, indent=4)
    with open(filename, "r") as file:
        return json.load(file)

def save_data(filename, data):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)
class Goat:
    def __init__(self, x, y, speed, max_hunger, eating_rate, fertility):
        self.x = x
        self.y = y
        self.speed = speed
        self.hunger = 0  # Уровень голода (0 - сытый)
        self.max_hunger = max_hunger  # Максимальный уровень голода, при котором коза умирает
        self.eating_rate = eating_rate
        self.fertility = fertility

class Cabbage:
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size

    def decrease_size(self, amount):
        self.size -= amount
        if self.size <= 0:
            return False  # Капуста полностью съедена
        return True  # Капуста еще есть

class Herd:
    def __init__(self, goats):
        self.goats = goats
        self.reproduction_timer = 0

    def update_hunger(self, status_bar=None):
        alive_goats = []
        for goat in self.goats:
            goat.hunger += 0.5  # Коза становится голоднее
            if goat.hunger < goat.max_hunger:
                alive_goats.append(goat)
            else:
                message = f"Коза умерла от голода: x={goat.x:.2f}, y={goat.y:.2f}"
                logging.debug(message)
                if status_bar:
                    status_bar.showMessage(message, 5000)
        self.goats = alive_goats
        logging.debug(f"Обновлено стадо: осталось {len(self.goats)} коз.")

    def get_center_and_radius(self):
        if not self.goats:
            return 0, 0, 0

        x_coords = [goat.x for goat in self.goats]
        y_coords = [goat.y for goat in self.goats]
        center_x = sum(x_coords) / len(x_coords)
        center_y = sum(y_coords) / len(y_coords)
        radius = max(
            ((goat.x - center_x) ** 2 + (goat.y - center_y) ** 2) ** 0.5
            for goat in self.goats
        )
        return center_x, center_y, max(radius, 20)

    def move_goats_towards(self, target):
        for goat in self.goats:
            dx = target.x - goat.x
            dy = target.y - goat.y
            distance = (dx ** 2 + dy ** 2) ** 0.5
            if distance > 0:
                goat.x += (dx / distance) * goat.speed
                goat.y += (dy / distance) * goat.speed
                logging.debug(f"Коза переместилась к капусте: x={goat.x:.2f}, y={goat.y:.2f}")

    def reproduce_goats(self, status_bar=None):
        new_goats = []
        for goat in self.goats:
            if goat.hunger == 0 and random.random() < goat.fertility:
                new_x = goat.x + random.uniform(-5, 5)
                new_y = goat.y + random.uniform(-5, 5)
                new_goat = Goat(new_x, new_y, goat.speed, goat.max_hunger, goat.eating_rate, goat.fertility)
                new_goats.append(new_goat)
                message = f"Овца размножилась: x={new_x:.2f}, y={new_y:.2f}"
                logging.debug(message)
                if status_bar:
                    status_bar.showMessage(message, 5000)
        self.goats.extend(new_goats)
        if new_goats:
            logging.debug(f"Новое поколение: добавлено {len(new_goats)} овец.")

class Farm:
    def __init__(self, width, height, herds=None, cabbages=None):
        self.width = width
        self.height = height
        self.herds = herds if herds is not None else []  # Список стад
        self.cabbages = cabbages if cabbages is not None else []  # Список капуст
        self.growth_timer = 0

    def add_herd(self, herd):
        try:
            self.herds.append(herd)
            logging.debug(f"Добавлено новое стадо: количество овец={len(herd.goats)}, всего стад={len(self.herds)}")
        except Exception as e:
            logging.error(f"Ошибка при добавлении стада: {e}", exc_info=True)

    def update(self, status_bar=None):
        logging.debug(f"Обновление фермы: количество стад={len(self.herds)}, количество капуст={len(self.cabbages)}")

        if not self.herds:
            logging.debug("Все стада вымерли, ферма пуста.")
            self.growth_timer += 1
            if self.growth_timer >= 100:
                self.grow_cabbage()
                self.growth_timer = 0
            return

        self.growth_timer += 1
        if self.growth_timer >= 100:
            self.grow_cabbage()
            self.growth_timer = 0

        for herd in self.herds:
            if not herd.goats:
                continue

            herd.update_hunger(status_bar)  # Обновляем уровень голода коз

            if not self.cabbages:
                continue

            target = self.get_nearest_cabbage(herd)
            if target is None:
                continue

            herd.move_goats_towards(target)

            if self.is_near_herd(herd, target):
                total_eating = 0
                for goat in herd.goats:
                    amount = goat.eating_rate
                    target_alive = target.decrease_size(amount)
                    total_eating += amount
                    goat.hunger = 0  # Коза стала сытой
                    if not target_alive:
                        break
                if not target_alive:
                    self.cabbages.remove(target)
                    message = f"Капуста съедена полностью: x={target.x:.2f}, y={target.y:.2f}"
                    logging.debug(message)
                    if status_bar:
                        status_bar.showMessage(message, 5000)
                else:
                    logging.debug(f"Капуста уменьшилась: x={target.x:.2f}, y={target.y:.2f}, размер={target.size:.2f}")

                # Козы размножаются после еды
                herd.reproduce_goats(status_bar)

        # Удаляем стада без коз
        self.herds = [herd for herd in self.herds if herd.goats]

    def grow_cabbage(self):
        x = random.randint(0, self.width)
        y = random.randint(0, self.height)
        size = random.randint(10, 30)
        self.cabbages.append(Cabbage(x, y, size))

    def get_nearest_cabbage(self, herd):
        center_x, center_y, _ = herd.get_center_and_radius()
        return min(
            self.cabbages,
            key=lambda c: math.sqrt((c.x - center_x) ** 2 + (c.y - center_y) ** 2)
        )

    def is_near_herd(self, herd, target):
        center_x, center_y, radius = herd.get_center_and_radius()
        distance = math.sqrt((target.x - center_x) ** 2 + (target.y - center_y) ** 2)
        return distance <= radius

# Настройка логирования
logging.basicConfig(filename="debug.log", level=logging.DEBUG, filemode="w")

def main():
    logging.debug("Инициализация приложения...")
    data = load_initial_data("config.json")

    logging.debug("Создание объектов овец и капусты...")
    goat_defaults = data.get("goats", {})
    herds = []
    if "herds" in data:
        herds = [Herd([Goat(**goat_data) for goat_data in herd_data]) for herd_data in data.get("herds", [])]
    else:
        count = goat_defaults.get("count", 10)
        max_offset = 5  # Максимальное смещение от базовой точки

        # Определяем базовую точку с учетом смещения
        base_x = random.randint(max_offset, data["farm_size"]["width"] - max_offset)
        base_y = random.randint(max_offset, data["farm_size"]["height"] - max_offset)

        goats = [
            Goat(
                x=base_x + random.uniform(-max_offset, max_offset),
                y=base_y + random.uniform(-max_offset, max_offset),
                speed=goat_defaults.get("speed", 5.0),
                max_hunger=goat_defaults.get("max_hunger", 50),
                eating_rate=goat_defaults.get("eating_rate", 5.0),
                fertility=goat_defaults.get("fertility", 0.3)
            )
            for _ in range(count)
        ]
        herds = [Herd(goats)]

    cabbages = [Cabbage(**cabbage_data) for cabbage_data in data.get("cabbages", [])]
    if not cabbages:
        # Если капусты нет в данных, создаем капусту рядом с козами
        cabbages = [Cabbage(base_x + 50, base_y + 50, 20)]

    logging.debug("Создание фермы...")
    farm = Farm(data["farm_size"]["width"], data["farm_size"]["height"], herds, cabbages)

    app = QApplication([])
    # Применяем стиль Fusion
    app.setStyle('Fusion')

    # Настраиваем палитру
    from PyQt5.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)

    window = MainWindow(farm)
    window.show()
    app.exec_()

if __name__ == "__main__":
    main()
