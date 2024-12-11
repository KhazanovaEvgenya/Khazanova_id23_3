#Вариант 15
import tkinter as tk
from tkinter import ttk
import math

def min_max_height(v, m, v0, t):
    rho_air = 1.225
    g = 9.81

    F_lift = v * rho_air * g

    F_gravity = m * g

    h = v0 * t + (t**2 * (F_lift - F_gravity)) / (2 * m)
    return max(h, 0)

def animate_object():
    global animation_running, time, object
    if not animation_running:
        return

    time += 0.07
    h = min_max_height(obiem.get(), masa.get(), speed.get(), time)

    canvas_height = canvas.winfo_height()
    new_y = canvas_height - h * scale_factor

    if new_y < 0:
        animation_running = False
        return

    canvas.coords(object, 90, new_y, 110, new_y - 20)
    root.after(50, animate_object)

def start_animation():
    global animation_running, time
    animation_running = True
    time = 0
    animate_object()

def reset_object():
    global animation_running
    animation_running = False
    canvas.coords(object, 90, 380, 110, 360)

root = tk.Tk()
root.title("Воздушный шар")

# Переменные
obiem = tk.DoubleVar(value=1.0)  # Объем шара (м^3)
masa = tk.DoubleVar(value=1.0)  # Масса груза (кг)
speed = tk.DoubleVar(value=15.0)  # Начальная скорость (м/с)

animation_running = False
scale_factor = 10

frame = ttk.Frame(root)
frame.pack(pady=10)

ttk.Label(frame, text="Объем шара:").grid(row=0, column=0)
obiem_slider = ttk.Scale(frame, from_=0.1, to=10, variable=obiem, orient="horizontal")
obiem_slider.grid(row=0, column=1)

ttk.Label(frame, text="Масса груза:").grid(row=1, column=0)
masa_slider = ttk.Spinbox(frame, from_=0.1, to=50, textvariable=masa, increment=0.1)
masa_slider.grid(row=1, column=1)

ttk.Label(frame, text="Начальная скорость:").grid(row=2, column=0)
speed_slider = ttk.Scale(frame, from_=0, to=20, variable=speed, orient="horizontal")
speed_slider.grid(row=2, column=1)

start_klick = ttk.Button(frame, text="Запуск", command=start_animation)
start_klick.grid(row=3, column=0, pady=10)

sbros = ttk.Button(frame, text="Сброс", command=reset_object)
sbros.grid(row=3, column=1, pady=10)

canvas = tk.Canvas(root, width=200, height=400, bg="skyblue")
canvas.pack()

object = canvas.create_oval(90, 380, 110, 360, fill="pink")

time = 0

root.mainloop()
