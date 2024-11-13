import math
import sys
from random import random
import math

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter, QBrush, QColor
from PyQt6.QtWidgets import QApplication, QWidget


class CircleAnimation(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Sheeps Animation')
        self.setGeometry(100, 100, 600, 600)
        self.radius = 200  # радиус окружности
        self.center_x = self.width() // 2
        self.center_y = self.height() // 2
        self.speed = 7  # скорость анимации

        self.cabbages = [Cabbage(self.radius, [self.center_x, self.center_y]) for _ in range(5)]
        self.sheeps = [Sheep(self.radius, [self.center_x, self.center_y])]
        # Таймер
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_position)
        self.timer.start(16)

    def update_position(self):
        self.update()

    def add_cabbage(self):
        new_cabbage = Cabbage(self.radius, [self.center_x, self.center_y])

        # перекрытия с другими капустами
        while any(self.is_overlapping(new_cabbage, existing) for existing in self.cabbages):
            new_cabbage.generate_coords()  # новые координаты, если есть перекрытие
        return new_cabbage

    def is_overlapping(self, cabbage1, cabbage2):
        distance = math.sqrt((cabbage1.x - cabbage2.x) ** 2 + (cabbage1.y - cabbage2.y) ** 2)
        # проверка на пересечение
        return distance < cabbage1.size + cabbage2.size

    def get_purpose_cabbage(self):
        min_distance = float('inf')
        nearest_cabbage = None

        for cabbage in self.cabbages:
            for sheep in self.sheeps:
                distance = math.sqrt((cabbage.x - sheep.x) ** 2 + (cabbage.y - sheep.y) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    nearest_cabbage = cabbage

        return nearest_cabbage

    def paintEvent(self, event, **kwargs):
        painter = QPainter(self)

        # окружность
        painter.setBrush(QBrush(Qt.GlobalColor.white, Qt.BrushStyle.SolidPattern))
        painter.drawEllipse(self.center_x - self.radius, self.center_y - self.radius, self.radius * 2, self.radius * 2)
        self.purpose_cabbage = self.get_purpose_cabbage()
        for cabbage in self.cabbages:
            # капусты
            cabbage_x = cabbage.x
            cabbage_y = cabbage.y

            painter.setBrush(QBrush(QColor(0, 255, 0), Qt.BrushStyle.SolidPattern))
            painter.drawEllipse(int(cabbage_x - 5), int(cabbage_y) - 5, int(cabbage.size), int(cabbage.size))

        # расстояние
        distances = self.sheeps_going()

        # копия списка овец
        sheeps_copy = self.sheeps[:]

        for id, sheep in enumerate(sheeps_copy):
            if sheep.hungry <= 0:
                sheep.exist = False
                self.sheeps.remove(sheep)
                Sheep.SHEEP_COUNT -= 1
                if Sheep.SHEEP_COUNT == 0:
                    print("All sheep dead. Unlucky :(")
                    sys.exit(app.exec())
            else:
                sheep_x = sheep.x
                sheep_y = sheep.y

                if id < len(distances) and distances[id] < 20:
                    sheep.hungry += sheep.eat_speed
                    self.purpose_cabbage.value -= sheep.eat_speed
                    if self.purpose_cabbage.value <= 0:
                        self.cabbages.remove(self.purpose_cabbage)
                        self.purpose_cabbage = self.add_cabbage()
                        self.cabbages.append(self.purpose_cabbage)
                else:
                    sheep.hungry -= 1  # уменьшение голода овец

                if sheep.hungry > sheep.reproduction_threshold:
                    sheep.hungry -= 300
                    sheep.size += 10
                painter.setBrush(QBrush(QColor(0, 0, 0), Qt.BrushStyle.SolidPattern))
                painter.drawEllipse(int(sheep_x - 5), int(sheep_y - 5), sheep.size, sheep.size)

    def sheeps_going(self):
        distance_list = []
        for sheep in self.sheeps:
            dx = self.purpose_cabbage.x - sheep.x
            dy = self.purpose_cabbage.y - sheep.y

            distance = math.sqrt(dx ** 2 + dy ** 2)
            distance_list.append(distance)
            if distance > self.purpose_cabbage.size - 2:
                sheep.x += sheep.speed * (dx / distance)
                sheep.y += sheep.speed * (dy / distance)
        return distance_list



class Cabbage:
    def __init__(self, circle_radius, center):
        self.center = center
        self.circle_radius = circle_radius
        self.exist = False
        self.generate_coords()
        self.value = int((random() + 0.1) * 400)
        self.size = 2 * math.log(self.value)

    def generate_coords(self):
        range = random() * (self.circle_radius * 0.95)
        angle = random() * 360
        self.x = self.center[0] + range * math.cos(math.radians(angle))
        self.y = self.center[1] + range * math.sin(math.radians(angle))
        self.value = int((random() + 0.1) * 400)


class Sheep:
    SHEEP_COUNT = 0

    def __init__(self, circle_radius, center):
        Sheep.SHEEP_COUNT += 1
        self.center = center
        self.circle_radius = circle_radius
        self.speed = random()  # Скорость
        self.hungry = (random() + 0.1) * 1000  # Голод
        self.reproduction_threshold = (random() + 0.1) * 2000  # для увеличения стада в зависимости от сытости
        self.eat_speed = random() + 1  # скорость поедания
        self.generate_coords()  #координаты овцы
        print(f'{self.reproduction_threshold};\nEat speed: {self.eat_speed};\nTOTAL SHEEPS: {Sheep.SHEEP_COUNT}')
        self.size = int(self.hungry // 40)

    def generate_coords(self):
        range = random() * (self.circle_radius * 0.95)
        angle = random() * 360
        self.x = self.center[0] + range * math.cos(math.radians(angle))
        self.y = self.center[1] + range * math.sin(math.radians(angle))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CircleAnimation()
    window.show()
    sys.exit(app.exec())
