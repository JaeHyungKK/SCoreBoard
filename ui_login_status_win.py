# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from core.db import *
from core.sys_config import *
from functools import partial


class LoginStatusWindow(QDialog):

    def __init__(self, user_id, *args, **kwargs):
        super(LoginStatusWindow, self).__init__(*args, **kwargs)
        self.ls = None
        self.login_success = None
        self.user_id = user_id

        self.ui()

        # 스타트업 메소드
        self.init_alives()

    def ui(self):
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(QIcon('image/scoreboard_16.png'))

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignTop)

        self.main_scroll = QScrollArea()
        self.main_scroll.setWidget(QWidget())
        self.main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.main_scroll.setWidgetResizable(True)

        self.scroll_layout = QVBoxLayout(self.main_scroll.widget())
        self.scroll_layout.setAlignment(Qt.AlignTop)

        self.setFixedSize(600, 300)

        main_font = QFont()
        main_font.setFamily("Malgun Gothic")
        main_font.setStyleStrategy(QFont.PreferQuality)

        self.main_layout.addWidget(self.main_scroll)

    def init_alives(self):
        """로그인 여부를 확인하는 메소드"""
        import socket
        self.lan_ip = socket.gethostbyname(socket.getfqdn())

        # 위젯 clear
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            widget = item.widget()
            widget.setParent(None)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT hostname, private_ip, public_ip FROM alives WHERE score_user_account=%s',
            (self.user_id,),
        )
        results = cursor.fetchall()

        if not results:
            return

        for hostname, private, public in reversed(results):

            login_status_gb = QGroupBox()
            login_status_gb.setStyleSheet("background-color: White;")
            login_status_layout = QHBoxLayout(login_status_gb)

            user_info_text = QLabel(u'사용자: {}   내부 IP: {}    외부 IP: {}'.format(hostname, private, public))

            label = QLabel(u"현재 사용중인 PC")
            label.adjustSize()
            label.setStyleSheet("font: 11pt; color:#060FFF;")
            label.setAlignment(Qt.AlignCenter)

            btn = QPushButton(u'{} 원격 종료'.format(hostname))
            btn.setFixedSize(180, 30)
            btn.setStyleSheet("background-color: #1565C0;\n"     
                                 "border-radius:2px;\n"
                                 # "font: 11pt;\n"
                                 "font-weight: 900;\n"
                                 "border: 1.6px outset #1B4F72;\n"
                                 "color: White;")
            btn.adjustSize()
            btn.clicked.connect(partial(self.disconnect_login_info, hostname, private, public))

            login_status_layout.addWidget(user_info_text)
            if self.lan_ip == private:
                login_status_layout.addWidget(label)
            else:
                login_status_layout.addWidget(btn)
            self.scroll_layout.addWidget(login_status_gb)

    def disconnect_login_info(self, hostname, private, public):
        """원격 종료를 하는 메소드"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM alives WHERE hostname=%s AND private_ip=%s AND public_ip=%s',
            (hostname, private, public),
        )

        if self.lan_ip == private:
            return

        conn.commit()
        self.init_alives()

