import math

from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QColor,
    QRadialGradient,
    QPainterPath,
)
from PyQt6.QtWidgets import QWidget


class AIOrb(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumSize(300, 300)

        self.state = "idle"

        self.rotation = 0.0
        self.pulse = 0.0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)

    # =====================================================
    # STATE
    # =====================================================

    def set_state(self, state):

        self.state = state.lower()
        self.update()

    # =====================================================
    # ANIMATION
    # =====================================================

    def animate(self):

        if self.state == "speaking":
            self.rotation += 0.045
            self.pulse += 0.14

        elif self.state == "listening":
            self.rotation += 0.025
            self.pulse += 0.09

        else:
            self.rotation += 0.008
            self.pulse += 0.045

        self.update()

    # =====================================================
    # MANGEKYO PATTERN
    # =====================================================

    def draw_pattern(
        self,
        painter,
        cx,
        cy,
        radius
    ):

        painter.save()

        painter.translate(cx, cy)

        painter.rotate(
            math.degrees(
                self.rotation
            )
        )

        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        painter.setPen(
            QPen(
                QColor(5, 0, 0),
                8,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin
            )
        )

        # Three curved Mangekyo blades
        for i in range(3):

            angle = (
                i * math.pi * 2 / 3
            )

            path = QPainterPath()

            # Start near center
            sx = math.cos(angle) * 7
            sy = math.sin(angle) * 7

            path.moveTo(
                sx,
                sy
            )

            # First curve
            x1 = math.cos(
                angle + 0.20
            ) * radius * 0.38

            y1 = math.sin(
                angle + 0.20
            ) * radius * 0.38

            # Second curve
            x2 = math.cos(
                angle + 0.55
            ) * radius * 0.68

            y2 = math.sin(
                angle + 0.55
            ) * radius * 0.68

            # Outer tip
            x3 = math.cos(
                angle + 0.95
            ) * radius * 0.90

            y3 = math.sin(
                angle + 0.95
            ) * radius * 0.90

            path.cubicTo(
                x1,
                y1,
                x2,
                y2,
                x3,
                y3
            )

            painter.drawPath(
                path
            )

        painter.restore()

    # =====================================================
    # PAINT
    # =====================================================

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        cx = self.width() / 2
        cy = self.height() / 2

        # =================================================
        # INTENSITY
        # =================================================

        if self.state == "speaking":
            intensity = 1.0

        elif self.state == "listening":
            intensity = 0.85

        else:
            intensity = 0.55

        pulse = (
            math.sin(self.pulse) + 1
        ) / 2

        # =================================================
        # OUTER RED GLOW
        # =================================================

        glow_radius = (
            135 +
            pulse * 20 * intensity
        )

        glow = QRadialGradient(
            cx,
            cy,
            glow_radius
        )

        glow.setColorAt(
            0.0,
            QColor(
                255,
                0,
                15,
                int(105 * intensity)
            )
        )

        glow.setColorAt(
            0.30,
            QColor(
                220,
                0,
                20,
                int(65 * intensity)
            )
        )

        glow.setColorAt(
            0.60,
            QColor(
                120,
                0,
                15,
                int(25 * intensity)
            )
        )

        glow.setColorAt(
            1.0,
            QColor(
                0,
                0,
                0,
                0
            )
        )

        painter.setPen(
            Qt.PenStyle.NoPen
        )

        painter.setBrush(
            QBrush(glow)
        )

        painter.drawEllipse(
            QRectF(
                cx - glow_radius,
                cy - glow_radius,
                glow_radius * 2,
                glow_radius * 2
            )
        )

        # =================================================
        # OUTER BLACK RIM
        # =================================================

        outer_radius = 105

        painter.setBrush(
            QColor(
                8,
                0,
                0
            )
        )

        painter.setPen(
            QPen(
                QColor(
                    255,
                    25,
                    35,
                    220
                ),
                3
            )
        )

        painter.drawEllipse(
            QRectF(
                cx - outer_radius,
                cy - outer_radius,
                outer_radius * 2,
                outer_radius * 2
            )
        )

        # =================================================
        # RED IRIS
        # =================================================

        iris_radius = 96

        iris = QRadialGradient(
            cx - 22,
            cy - 25,
            iris_radius
        )

        iris.setColorAt(
            0.0,
            QColor(
                255,
                105,
                105
            )
        )

        iris.setColorAt(
            0.22,
            QColor(
                255,
                45,
                50
            )
        )

        iris.setColorAt(
            0.55,
            QColor(
                220,
                5,
                20
            )
        )

        iris.setColorAt(
            0.82,
            QColor(
                145,
                0,
                12
            )
        )

        iris.setColorAt(
            1.0,
            QColor(
                65,
                0,
                5
            )
        )

        painter.setBrush(
            QBrush(iris)
        )

        painter.setPen(
            QPen(
                QColor(
                    20,
                    0,
                    0
                ),
                4
            )
        )

        painter.drawEllipse(
            QRectF(
                cx - iris_radius,
                cy - iris_radius,
                iris_radius * 2,
                iris_radius * 2
            )
        )

        # =================================================
        # IRIS RINGS
        # =================================================

        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        painter.setPen(
            QPen(
                QColor(
                    85,
                    0,
                    5,
                    180
                ),
                2
            )
        )

        for ratio in (
            0.34,
            0.57,
            0.78
        ):

            r = iris_radius * ratio

            painter.drawEllipse(
                QRectF(
                    cx - r,
                    cy - r,
                    r * 2,
                    r * 2
                )
            )

        # =================================================
        # MANGEKYO PATTERN
        # =================================================

        self.draw_pattern(
            painter,
            cx,
            cy,
            iris_radius
        )

        # =================================================
        # CENTRAL PUPIL
        # =================================================

        pupil_radius = 25

        pupil = QRadialGradient(
            cx - 4,
            cy - 4,
            pupil_radius
        )

        pupil.setColorAt(
            0.0,
            QColor(
                35,
                0,
                0
            )
        )

        pupil.setColorAt(
            0.65,
            QColor(
                5,
                0,
                0
            )
        )

        pupil.setColorAt(
            1.0,
            QColor(
                0,
                0,
                0
            )
        )

        painter.setBrush(
            QBrush(pupil)
        )

        painter.setPen(
            Qt.PenStyle.NoPen
        )

        painter.drawEllipse(
            QRectF(
                cx - pupil_radius,
                cy - pupil_radius,
                pupil_radius * 2,
                pupil_radius * 2
            )
        )

        # =================================================
        # INNER RED CORE
        # =================================================

        core = (
            10 +
            pulse * 3
        )

        core_gradient = QRadialGradient(
            cx - 3,
            cy - 3,
            core
        )

        core_gradient.setColorAt(
            0.0,
            QColor(
                255,
                240,
                240
            )
        )

        core_gradient.setColorAt(
            0.25,
            QColor(
                255,
                70,
                70
            )
        )

        core_gradient.setColorAt(
            1.0,
            QColor(
                120,
                0,
                0
            )
        )

        painter.setBrush(
            QBrush(core_gradient)
        )

        painter.drawEllipse(
            QRectF(
                cx - core,
                cy - core,
                core * 2,
                core * 2
            )
        )

        # =================================================
        # HIGHLIGHT
        # =================================================

        painter.setBrush(
            QColor(
                255,
                235,
                235,
                220
            )
        )

        painter.drawEllipse(
            QRectF(
                cx - 38,
                cy - 48,
                10,
                10
            )
        )

        painter.end()


# Compatibility
AetherOrb = AIOrb