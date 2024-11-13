

import sys
import math

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QBrush, QColor

class CircleAnimation(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Circle Animation')
        self.setGeometry(100, 100, 600, 600)
        self.angle = 0  # начальный угол
        self.radius = 200  # радиус окружности
        self.center_x = self.width() // 2
        self.center_y = self.height() // 2
        self.speed = 2  # скорость анимации, положительное значение для движения по часовой, отрицательное для против часовой

        # Таймер для обновления положения точки
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_position)
        self.timer.start(10)  # обновление каждые 30 миллисекунд

    def update_position(self):
        self.angle += self.speed
        if self.angle >= 360:
            self.angle = 0
        elif self.angle < 0:
            self.angle = 360

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        # Рисуем окружность
        painter.setBrush(QBrush(Qt.GlobalColor.white, Qt.BrushStyle.SolidPattern))
        painter.drawEllipse(self.center_x - self.radius, self.center_y - self.radius, self.radius * 2, self.radius * 2)

        # Координаты движущейся точки по окружности
        point_x = self.center_x + self.radius * math.cos(math.radians(self.angle))
        point_y = self.center_y + self.radius * math.sin(math.radians(self.angle))

        # Рисуем точку
        painter.setBrush(QBrush(QColor(255, 0, 0), Qt.BrushStyle.SolidPattern))
        painter.drawEllipse(int(point_x - 5), int(point_y) - 5, 10, 10)  # точка диаметром 10 пикселей

    def keyPressEvent(self, event):
        # Управление скоростью анимации с помощью стрелок
        if event.key() == Qt.Key.Key_Up:
            self.speed += 1  # Увеличение скорости
        elif event.key() == Qt.Key.Key_Down:
            self.speed -= 1  # Уменьшение скорости


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CircleAnimation()
    window.show()
    sys.exit(app.exec())