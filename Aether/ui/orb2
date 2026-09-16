from PyQt6.QtCore import (
    Qt,
    QTimer,
    QPointF
)

from PyQt6.QtGui import (
    QPainter,
    QRadialGradient,
    QColor,
    QPen
)

from PyQt6.QtWidgets import QWidget

import math


class AIOrb(QWidget):

    def __init__(self):

        super().__init__()

        self.state = "idle"

        self.angle = 0

        self.pulse = 0

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.animate
        )

        self.timer.start(30)

        self.setMinimumSize(
            320,
            320
        )

    def set_state(self, state):

        self.state = state

        self.update()

    def animate(self):

        self.angle += 3

        self.pulse += 0.08

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        cx = self.width() / 2
        cy = self.height() / 2

        center = QPointF(
            cx,
            cy
        )

        # State colors

        if self.state == "listening":

            color = QColor(
                0,
                210,
                255
            )

            pulseSpeed = 1.0

        elif self.state == "thinking":

            color = QColor(
                155,
                90,
                255
            )

            pulseSpeed = 1.4

        elif self.state == "speaking":

            color = QColor(
                0,
                255,
                180
            )

            pulseSpeed = 1.8

        else:

            color = QColor(
                35,
                130,
                255
            )

            pulseSpeed = 0.7

        pulse = (
            math.sin(
                self.pulse * pulseSpeed
            ) + 1
        ) / 2

        # Outer glow

        gradient = QRadialGradient(
            center,
            145
        )

        gradient.setColorAt(
            0.0,
            QColor(
                color.red(),
                color.green(),
                color.blue(),
                100
            )
        )

        gradient.setColorAt(
            0.35,
            QColor(
                color.red(),
                color.green(),
                color.blue(),
                40
            )
        )

        gradient.setColorAt(
            1.0,
            QColor(
                color.red(),
                color.green(),
                color.blue(),
                0
            )
        )

        painter.setPen(
            QPen(
                Qt.PenStyle.NoPen
            )
        )

        painter.setBrush(
            gradient
        )

        painter.drawEllipse(
            center,
            145 + pulse * 10,
            145 + pulse * 10
        )

        # Rotating rings

        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        painter.setPen(
            QPen(
                QColor(
                    color.red(),
                    color.green(),
                    color.blue(),
                    90
                ),
                2
            )
        )

        painter.drawEllipse(
            center,
            92 + pulse * 5,
            92 + pulse * 5
        )

        painter.setPen(
            QPen(
                QColor(
                    color.red(),
                    color.green(),
                    color.blue(),
                    45
                ),
                1
            )
        )

        painter.drawEllipse(
            center,
            115,
            115
        )

        # Core

        coreGradient = QRadialGradient(
            center,
            45
        )

        coreGradient.setColorAt(
            0.0,
            QColor(
                255,
                255,
                255,
                255
            )
        )

        coreGradient.setColorAt(
            0.2,
            QColor(
                color.red(),
                color.green(),
                color.blue(),
                255
            )
        )

        coreGradient.setColorAt(
            1.0,
            QColor(
                color.red(),
                color.green(),
                color.blue(),
                120
            )
        )

        painter.setBrush(
            coreGradient
        )

        painter.setPen(
            Qt.PenStyle.NoPen
        )

        painter.drawEllipse(
            center,
            42 + pulse * 3,
            42 + pulse * 3
        )

        # Orbit particles

        for i in range(8):

            angle = math.radians(
                self.angle + i * 45
            )

            radius = 105

            x = (
                cx
                + math.cos(angle)
                * radius
            )

            y = (
                cy
                + math.sin(angle)
                * radius
            )

            painter.setBrush(
                QColor(
                    color.red(),
                    color.green(),
                    color.blue(),
                    180
                )
            )

            painter.drawEllipse(
                QPointF(x, y),
                3,
                3
            )

        painter.end()
