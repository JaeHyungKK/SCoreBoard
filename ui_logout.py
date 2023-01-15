# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from core.db import *
from core.sys_config import *
import sys
import subprocess


class LogoutWindow(QDialog):
    def __init__(self, user_id, *args, **kwargs):
        super(LogoutWindow, self).__init__(*args, **kwargs)
        self.is_logout = False
        self.user_id = user_id
        self.setup_ui()
        self.init_alives()

    def setup_ui(self):

        font = QFont()
        font.setFamily("Malgun Gothic")
        font.setStyleStrategy(QFont.PreferQuality)
        font.setPointSize(9)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignTop)

        self.main_scroll = QScrollArea()
        self.main_scroll.setWidget(QWidget())
        self.main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.main_scroll.setWidgetResizable(True)

        self.scroll_layout = QFormLayout(self.main_scroll.widget())
        self.scroll_layout.setAlignment(Qt.AlignTop)

        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(QIcon('image/scoreboard_16.png'))

        # 위젯 최소화 최대화
        self.setWindowFlags(Qt.CustomizeWindowHint |
                            Qt.WindowMinimizeButtonHint |
                            Qt.WindowMaximizeButtonHint |
                            Qt.WindowCloseButtonHint)

        self.main_layout.addWidget(self.main_scroll)
        self.setFixedSize(360, 315)

        self.show()

    def init_alives(self):
        """
        설정에서 네트워크 드라이브 연결 버튼을 클릭 시
        사용자가 사용중인 네트워크 드라이브의 전체 정보를 불러온다.
        """

        conn = get_con_smart_maker()
        curs = conn.cursor()
        curs.execute(
            'SELECT '
            '   n.drive, '
            '   s.private_ip, '
            '   n.description '
            'FROM connections c '
            'LEFT JOIN netdrive n ON n.id=c.netdrive_id '
            'LEFT JOIN users u ON u.id=c.users_id '
            'LEFT JOIN server s ON s.id=n.server_id '
            'WHERE '
            ' u.id LIKE %s',
            (self.user_id,)
        )
        results = curs.fetchall()
        if not results:
            return

        connections_info = subprocess.Popen(u'net use',
                                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        connections_info, err = connections_info.communicate()
        connections_info = str(connections_info, 'euc-kr')
        connections_info = connections_info.split('\n')
        current_status_data = {}

        for line in connections_info:
            if line.startswith(u'OK'):
                c_line = line
                c_line = c_line.strip()
                c_line = c_line.split('\\')
                connected_ip = c_line[2]
                d_line = c_line[0]
                d_line = d_line.split('           ')
                d_line = d_line[1].split(':')
                connected_drive = d_line[0]
                current_status_data[connected_drive] = connected_ip

        for drive_name, private_ip, description in results:
            login_status_gb = QGroupBox()
            login_status_gb.setStyleSheet("background-color: White;")
            login_status_layout = QHBoxLayout(login_status_gb)

            user_info_text = QLabel(u'드라이브: {}   서버: {}'.format(drive_name, description))

            conn_label = QLabel(u"연결 완료")
            conn_label.adjustSize()
            conn_label.setStyleSheet("font: 10pt; color:#060FFF;")
            conn_label.setAlignment(Qt.AlignCenter)
            conn_label.setAlignment(Qt.AlignRight)

            disconn_label = QLabel(u"연결 실패")
            disconn_label.adjustSize()
            disconn_label.setStyleSheet("font: 10pt; color:#FF0000;")
            disconn_label.setAlignment(Qt.AlignRight)

            login_status_layout.addWidget(user_info_text)

            label = disconn_label
            if drive_name in current_status_data:
                if private_ip == current_status_data[drive_name]:
                    label = conn_label

            login_status_layout.addWidget(label)

            self.scroll_layout.addWidget(login_status_gb)

    def closeEvent(self, event):
        pass

    def showEvent(self, event):
        self.showNormal()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = LogoutWindow()
    win.exec_()
    sys.exit()
