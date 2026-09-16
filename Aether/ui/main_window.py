from PyQt6.QtCore import (
    Qt,
    QTimer,
    pyqtSignal,
    QEasingCurve,
    QPropertyAnimation,
    QRect
)

from PyQt6.QtWidgets import (
    QLineEdit,
    QPushButton,
    QHBoxLayout,
)

from PyQt6.QtGui import (
    QFont,
    QColor,
    QPainter,
    QPen,
    QBrush
)

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QFrame,
    QGraphicsDropShadowEffect,
    QSizePolicy
)

from ui.orb import AIOrb


class Waveform(QWidget):

    def __init__(self):
        super().__init__()

        self.level = 0
        self.active = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wave)

        self.timer.start(70)

        self.setMinimumHeight(55)

    def set_active(self, active):
        self.active = active
        self.update()

    def update_wave(self):

        if self.active:
            self.level += 1

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        width = self.width()
        height = self.height()

        bars = 35

        spacing = width / bars

        for i in range(bars):

            if self.active:

                import math

                value = (
                    abs(
                        math.sin(
                            self.level * 0.15 + i * 0.55
                        )
                    )
                    * 22
                )

            else:

                value = 3

            x = i * spacing

            y = height / 2 - value / 2

            painter.setPen(
                QPen(
                    QColor(
                        0,
                        180,
                        255,
                        190
                    ),
                    3
                )
            )

            painter.drawLine(
                int(x),
                int(y),
                int(x),
                int(y + value)
            )

        painter.end()


class MainWindow(QMainWindow):

    audio_signal = pyqtSignal(bytes)
    text_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)

    def __init__(self):

        super().__init__()

        self.messages = []

        self.current_user_message = None
        self.current_ai_message = None

        self.setWindowTitle(
            "Aether AI"
        )

        self.resize(
            1350,
            820
        )

        self.setMinimumSize(
            1050,
            700
        )

        self.setStyleSheet("""

        QMainWindow {
            background: #03050a;
        }

        QWidget {
            color: #eaf6ff;
            font-family: "Segoe UI";
        }

        QFrame#sidebar {
            background: #070a11;
            border-right: 1px solid #111b2b;
        }

        QLabel#brand {
            font-size: 25px;
            font-weight: 800;
            color: #ffffff;
        }

        QLabel#brandSub {
            font-size: 10px;
            letter-spacing: 2px;
            color: #536781;
        }

        QLabel#section {
            color: #43536c;
            font-size: 10px;
            font-weight: 700;
            padding-left: 12px;
        }

        QPushButton#nav {
            background: transparent;
            color: #72839e;
            border: none;
            border-radius: 9px;
            padding: 13px;
            text-align: left;
            font-size: 13px;
        }

        QPushButton#nav:hover {
            background: #0d1420;
            color: #dff7ff;
        }

        QPushButton#navActive {
            background: #0c1726;
            color: #00c8ff;
            border: 1px solid #12334b;
            border-radius: 9px;
            padding: 13px;
            text-align: left;
            font-size: 13px;
        }

        QFrame#topbar {
            background: #060912;
            border-bottom: 1px solid #111b2b;
        }

        QLabel#pageTitle {
            font-size: 19px;
            font-weight: 700;
        }

        QLabel#status {
            color: #00e0a4;
            background: #071b18;
            border: 1px solid #0c4238;
            border-radius: 14px;
            padding: 7px 13px;
            font-size: 11px;
        }

        QFrame#glass {
            background: #080d16;
            border: 1px solid #142238;
            border-radius: 18px;
        }

        QLabel#orbTitle {
            font-size: 12px;
            color: #647894;
            letter-spacing: 1px;
        }

        QLabel#aiName {
            font-size: 26px;
            font-weight: 700;
        }

        QLabel#aiDescription {
            color: #65758d;
            font-size: 12px;
        }

        QTextEdit#chat {
            background: #060a11;
            border: 1px solid #111d30;
            border-radius: 13px;
            padding: 14px;
            color: #c9d8e8;
            font-size: 13px;
        }

        QFrame#voicePanel {
            background: #070d16;
            border: 1px solid #15263c;
            border-radius: 17px;
        }

        QLabel#listenLabel {
            color: #8ca0b9;
            font-size: 12px;
        }

        QPushButton#mic {
            background: #008cff;
            border: none;
            border-radius: 31px;
            color: white;
            font-size: 15px;
            font-weight: 700;
            padding: 17px 25px;
        }

        QPushButton#mic:hover {
            background: #12a0ff;
        }

        QPushButton#mic:pressed {
            background: #006fca;
        }

        QFrame#info {
            background: #070c14;
            border: 1px solid #121f32;
            border-radius: 12px;
        }

        QLabel#infoTitle {
            color: #4d627c;
            font-size: 10px;
        }

        QLabel#infoValue {
            color: #d6e8f5;
            font-size: 12px;
            font-weight: 600;
        }

        """)

        # =====================================================
        # TEXT CHAT
        # =====================================================

        self.message_input = QLineEdit()

        self.message_input.setPlaceholderText(
            "Talk to Aether..."
        )

        self.message_input.setStyleSheet("""
            QLineEdit {
                background: #07111c;
                color: white;
                border: 1px solid #16405c;
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 15px;
            }

            QLineEdit:focus {
                border: 1px solid #00c8ff;
            }
        """)

        self.send_button = QPushButton(
            "SEND"
        )

        self.send_button.setStyleSheet("""
            QPushButton {
                background: #087ea4;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 12px 20px;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #00a9d9;
            }

            QPushButton:pressed {
                background: #05627f;
            }
        """)

        self.chat_layout = QHBoxLayout()

        self.chat_layout.addWidget(
            self.message_input
        )

        self.chat_layout.addWidget(
            self.send_button
        )

        self.build_ui()

    def make_shadow(self, widget):

        shadow = QGraphicsDropShadowEffect()

        shadow.setBlurRadius(35)

        shadow.setOffset(
            0,
            8
        )

        shadow.setColor(
            QColor(
                0,
                100,
                180,
                35
            )
        )

        widget.setGraphicsEffect(
            shadow
        )

    def build_ui(self):

        root = QWidget()

        self.setCentralWidget(
            root
        )

        rootLayout = QHBoxLayout(
            root
        )

        rootLayout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        rootLayout.setSpacing(
            0
        )

        # ==================================================
        # SIDEBAR
        # ==================================================

        sidebar = QFrame()

        sidebar.setObjectName(
            "sidebar"
        )

        sidebar.setFixedWidth(
            235
        )

        sideLayout = QVBoxLayout(
            sidebar
        )

        sideLayout.setContentsMargins(
            18,
            28,
            18,
            22
        )

        # Brand

        brand = QLabel(
            "AETHER"
        )

        brand.setObjectName(
            "brand"
        )

        sideLayout.addWidget(
            brand
        )

        brandSub = QLabel(
            "INTELLIGENT VOICE SYSTEM"
        )

        brandSub.setObjectName(
            "brandSub"
        )

        sideLayout.addWidget(
            brandSub
        )

        sideLayout.addSpacing(
            42
        )

        section = QLabel(
            "WORKSPACE"
        )

        section.setObjectName(
            "section"
        )

        sideLayout.addWidget(
            section
        )

        sideLayout.addSpacing(
            8
        )

        # Navigation

        self.chatNav = QPushButton(
            "◈    Chat"
        )

        self.chatNav.setObjectName(
            "navActive"
        )

        self.voiceNav = QPushButton(
            "◉    Voice"
        )

        self.voiceNav.setObjectName(
            "nav"
        )

        self.memoryNav = QPushButton(
            "◇    Memory"
        )

        self.memoryNav.setObjectName(
            "nav"
        )

        self.settingsNav = QPushButton(
            "⚙    Settings"
        )

        self.settingsNav.setObjectName(
            "nav"
        )

        for button in [
            self.chatNav,
            self.voiceNav,
            self.memoryNav,
            self.settingsNav
        ]:

            sideLayout.addWidget(
                button
            )

        sideLayout.addSpacing(
            25
        )

        section2 = QLabel(
            "SYSTEM"
        )

        section2.setObjectName(
            "section"
        )

        sideLayout.addWidget(
            section2
        )

        sideLayout.addSpacing(
            8
        )

        systemButton = QPushButton(
            "▣    System Monitor"
        )

        systemButton.setObjectName(
            "nav"
        )

        sideLayout.addWidget(
            systemButton
        )

        sideLayout.addStretch()

        # System card

        systemCard = QFrame()

        systemCard.setObjectName(
            "info"
        )

        systemLayout = QVBoxLayout(
            systemCard
        )

        systemLayout.setContentsMargins(
            13,
            13,
            13,
            13
        )

        systemTitle = QLabel(
            "SYSTEM STATUS"
        )

        systemTitle.setObjectName(
            "infoTitle"
        )

        systemValue = QLabel(
            "●  ALL SYSTEMS ONLINE"
        )

        systemValue.setObjectName(
            "infoValue"
        )

        systemLayout.addWidget(
            systemTitle
        )

        systemLayout.addSpacing(
            4
        )

        systemLayout.addWidget(
            systemValue
        )

        sideLayout.addWidget(
            systemCard
        )

        rootLayout.addWidget(
            sidebar
        )

        # ==================================================
        # MAIN AREA
        # ==================================================

        mainArea = QWidget()

        mainLayout = QVBoxLayout(
            mainArea
        )

        mainLayout.setContentsMargins(
            25,
            18,
            25,
            18
        )

        mainLayout.setSpacing(
            16
        )

        # ==================================================
        # TOP BAR
        # ==================================================

        topBar = QFrame()

        topBar.setObjectName(
            "topbar"
        )

        topBarLayout = QHBoxLayout(
            topBar
        )

        topBarLayout.setContentsMargins(
            0,
            0,
            0,
            15
        )

        title = QLabel(
            "Voice Assistant"
        )

        title.setObjectName(
            "pageTitle"
        )

        topBarLayout.addWidget(
            title
        )

        topBarLayout.addStretch()

        self.status = QLabel(
            "●  CONNECTING"
        )

        self.status.setObjectName(
            "status"
        )

        topBarLayout.addWidget(
            self.status
        )

        mainLayout.addWidget(
            topBar
        )

        # ==================================================
        # CONTENT
        # ==================================================

        content = QHBoxLayout()

        content.setSpacing(
            18
        )

        # --------------------------
        # LEFT ORB PANEL
        # --------------------------

        orbPanel = QFrame()

        orbPanel.setObjectName(
            "glass"
        )

        orbPanel.setMinimumWidth(
            500
        )

        orbLayout = QVBoxLayout(
            orbPanel
        )

        orbLayout.setContentsMargins(
            25,
            25,
            25,
            25
        )

        orbTitle = QLabel(
            "AETHER CORE"
        )

        orbTitle.setObjectName(
            "orbTitle"
        )

        orbLayout.addWidget(
            orbTitle
        )

        orbLayout.addStretch()

        self.orb = AIOrb()

        orbLayout.addWidget(
            self.orb,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        self.aiName = QLabel(
            "Aether"
        )

        self.aiName.setObjectName(
            "aiName"
        )

        self.aiName.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        orbLayout.addWidget(
            self.aiName
        )

        self.aiDescription = QLabel(
            "Gemini Native Audio Intelligence"
        )

        self.aiDescription.setObjectName(
            "aiDescription"
        )

        self.aiDescription.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        orbLayout.addWidget(
            self.aiDescription
        )

        orbLayout.addSpacing(
            20
        )

        self.waveform = Waveform()

        orbLayout.addWidget(
            self.waveform
        )

        orbLayout.addStretch()

        self.make_shadow(
            orbPanel
        )

        content.addWidget(
            orbPanel,
            5
        )

        # --------------------------
        # RIGHT PANEL
        # --------------------------

        right = QVBoxLayout()

        right.setSpacing(
            15
        )

        # Conversation

        chatPanel = QFrame()

        chatPanel.setObjectName(
            "glass"
        )

        chatLayout = QVBoxLayout(
            chatPanel
        )

        chatLayout.setContentsMargins(
            18,
            18,
            18,
            18
        )

        chatHeader = QHBoxLayout()

        chatTitle = QLabel(
            "CONVERSATION"
        )

        chatTitle.setObjectName(
            "orbTitle"
        )

        chatHeader.addWidget(
            chatTitle
        )

        chatHeader.addStretch()

        chatModel = QLabel(
            "GEMINI 2.5"
        )

        chatModel.setObjectName(
            "orbTitle"
        )

        chatHeader.addWidget(
            chatModel
        )

        chatLayout.addLayout(
            chatHeader
        )

        self.transcript = QTextEdit()

        self.transcript.setObjectName(
            "chat"
        )

        self.transcript.setReadOnly(
            True
        )

        self.transcript.setPlaceholderText(
            "Your conversation will appear here..."
        )

        chatLayout.addWidget(
            self.transcript
        )

        right.addWidget(
            chatPanel,
            5
        )

        # --------------------------
        # TEXT MESSAGE INPUT
        # --------------------------

        messagePanel = QFrame()

        messagePanel.setObjectName(
            "voicePanel"
        )

        messageLayout = QHBoxLayout(
            messagePanel
        )

        messageLayout.setContentsMargins(
            10,
            10,
            10,
            10
        )

        messageLayout.setSpacing(
            10
        )

        messageLayout.addWidget(
            self.message_input,
            1
        )

        messageLayout.addWidget(
            self.send_button
        )

        right.addWidget(
            messagePanel
        )

        # --------------------------
        # VOICE PANEL
        # --------------------------

        voicePanel = QFrame()

        voicePanel.setObjectName(
            "voicePanel"
        )

        voiceLayout = QVBoxLayout(
            voicePanel
        )

        voiceLayout.setContentsMargins(
            20,
            18,
            20,
            18
        )

        voiceHeader = QHBoxLayout()

        listenText = QLabel(
            "VOICE CONTROL"
        )

        listenText.setObjectName(
            "orbTitle"
        )

        voiceHeader.addWidget(
            listenText
        )

        voiceHeader.addStretch()

        self.listenState = QLabel(
            "READY"
        )

        self.listenState.setObjectName(
            "listenLabel"
        )

        voiceHeader.addWidget(
            self.listenState
        )

        voiceLayout.addLayout(
            voiceHeader
        )

        voiceLayout.addSpacing(
            10
        )

        self.mic_button = QPushButton(
            "🎤   START LISTENING"
        )

        self.mic_button.setObjectName(
            "mic"
        )

        self.mic_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        voiceLayout.addWidget(
            self.mic_button
        )

        right.addWidget(
            voicePanel
        )

        # --------------------------
        # INFORMATION CARDS
        # --------------------------

        infoRow = QHBoxLayout()

        infoRow.setSpacing(
            10
        )

        cards = [
            ("MODEL", "Gemini 2.5 Flash"),
            ("VOICE", "Kore"),
            ("MODE", "Live Audio"),
            ("STATUS", "Connected")
        ]

        for titleText, valueText in cards:

            card = QFrame()

            card.setObjectName(
                "info"
            )

            cardLayout = QVBoxLayout(
                card
            )

            cardLayout.setContentsMargins(
                12,
                10,
                12,
                10
            )

            label = QLabel(
                titleText
            )

            label.setObjectName(
                "infoTitle"
            )

            value = QLabel(
                valueText
            )

            value.setObjectName(
                "infoValue"
            )

            cardLayout.addWidget(
                label
            )

            cardLayout.addWidget(
                value
            )

            infoRow.addWidget(
                card
            )

        right.addLayout(
            infoRow
        )

        content.addLayout(
            right,
            5
        )

        mainLayout.addLayout(
            content,
            1
        )

        # ==================================================
        # FOOTER
        # ==================================================

        footer = QHBoxLayout()

        footerText = QLabel(
            "AETHER AI  •  REAL-TIME INTELLIGENCE"
        )

        footerText.setObjectName(
            "orbTitle"
        )

        footer.addWidget(
            footerText
        )

        footer.addStretch()

        version = QLabel(
            "v1.0.0"
        )

        version.setObjectName(
            "orbTitle"
        )

        footer.addWidget(
            version
        )

        mainLayout.addLayout(
            footer
        )

        rootLayout.addWidget(
            mainArea
        )

    # ======================================================
    # UI METHODS
    # ======================================================

    def set_status(self, status):

        self.status.setText(
            f"●  {status}"
        )

        statusLower = status.lower()

        if "connected" in statusLower:

            self.listenState.setText(
                "READY"
            )

            self.orb.set_state(
                "idle"
            )

        elif "connecting" in statusLower:

            self.listenState.setText(
                "CONNECTING..."
            )

        elif "error" in statusLower:

            self.listenState.setText(
                "CONNECTION ERROR"
            )

            self.orb.set_state(
                "thinking"
            )

    def update_transcript(self, speaker, text):

        if not text:
            return

        if (
                self.messages
                and self.messages[-1]["speaker"] == speaker
                and self.messages[-1]["streaming"]
        ):

            self.messages[-1]["text"] = text

        else:

            self.messages.append({
                "speaker": speaker,
                "text": text,
                "streaming": True
            })

        self.render_transcript()

    def finish_transcript(self):

        if self.messages:
            self.messages[-1]["streaming"] = False

        self.render_transcript()

    def render_transcript(self):

        html = ""

        for message in self.messages:

            speaker = message["speaker"]

            text = message["text"]

            if speaker == "YOU":

                color = "#8fa7c2"

            else:

                color = "#00c8ff"

            html += f"""
            <div style="
                margin-bottom:16px;
                padding:13px;
                background:#080f19;
                border:1px solid #122238;
                border-radius:12px;
            ">

                <div style="
                    color:{color};
                    font-size:11px;
                    font-weight:bold;
                    margin-bottom:7px;
                ">
                    {speaker}
                </div>

                <div style="
                    color:#d5e2ef;
                    font-size:14px;
                    line-height:1.5;
                ">
                    {text}
                </div>

            </div>
            """

        self.transcript.setHtml(html)

        self.transcript.moveCursor(
            self.transcript.textCursor().MoveOperation.End
        )

    def set_listening(self, active):

        if active:

            self.listenState.setText(
                "LISTENING"
            )

            self.mic_button.setText(
                "🔴   STOP LISTENING"
            )

            self.orb.set_state(
                "listening"
            )

            self.waveform.set_active(
                True
            )

        else:

            self.listenState.setText(
                "READY"
            )

            self.mic_button.setText(
                "🎤   START LISTENING"
            )

            self.orb.set_state(
                "idle"
            )

            self.waveform.set_active(
                False
            )