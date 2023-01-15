# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

# from resource_rc import *

from core.db import *
from core.sys_config import *
from core.reg import Registry
from drive_connector import *

import subprocess
import threading


class LoginWindow(QDialog):

    def __init__(self, *args, **kwargs):
        super(LoginWindow, self).__init__(*args, **kwargs)
        self.ls = None
        self.login_success = None

        self.setup_ui()

        # 조건에 따라 레지스트리에서 저장되어있는 사용자 아이디를 가져와 복구한다.
        self.restore_user_id_from_registry()

    def save_id_to_registry(self):
        """로그인에 성공하면 아이디 정보를 레지스트리에 저장한다."""
        login_email = None
        remember_me = 0

        if self.check_save_id.isChecked():
            login_email = self.email_address
            remember_me = 1

        reg = Registry('Login')
        reg.set('logged_id', login_email)
        reg.set('remember_me', remember_me)

    def restore_user_id_from_registry(self):
        """레지스트리로부터 저장되어있는 아이디를 가져온다."""
        if self.check_save_id.isChecked():
            reg = Registry('Login')
            stored_user_id = reg.get('logged_id')
            self.input_id.setText(stored_user_id)
            self.input_pw.setFocus()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.setFixedSize(330, 305)
        self.setWindowIcon(QIcon('image/scoreboard_16.png'))

        self.font = QFont()
        self.font.setFamily("Malgun Gothic")
        self.font.setStyleStrategy(QFont.PreferQuality)
        self.font.setPointSize(9)

        # 기본 윈도우 타이틀
        self.setWindowTitle(WINDOW_TITLE)

        # ID, PW 입력창 그룹 박스
        self.login_gb = QGroupBox()
        self.login_gb_layout = QVBoxLayout(self.login_gb)
        self.login_gb.setObjectName("login_gb")
        self.main_layout.addWidget(self.login_gb)
        self.login_gb.setStyleSheet("background-color: White;")

        self.setWindowFlags(Qt.CustomizeWindowHint |
                            Qt.WindowMinMaxButtonsHint |
                            Qt.WindowMaximizeButtonHint |
                            Qt.WindowCloseButtonHint)

        self.image_logo = QLabel(self.login_gb)
        self.image_logo.setPixmap(QPixmap('image/logo.png').scaled(60, 70, Qt.KeepAspectRatioByExpanding,
                                                                     Qt.SmoothTransformation))
        self.image_logo.setAlignment(Qt.AlignCenter)
        self.login_gb_layout.addWidget(self.image_logo)

        # ID, PW 입력 라인 에디터
        self.input_id = QLineEdit()
        self.input_id.setMinimumSize(32, 30)
        self.input_id.setPlaceholderText(u'아이디')
        self.input_id.setFont(self.font)
        self.input_id.setFocus()
        self.input_id.setTextMargins(33, 0, 4, 1)
        self.input_id.setStyleSheet("border-radius:2px;\n"
                                    "border: 1.4px inset gray;\n"
                                    "background-color: WhiteSmoke;")
        self.login_gb_layout.addWidget(self.input_id)

        self.input_pw = QLineEdit()
        self.input_pw.setMinimumSize(32, 30)
        self.input_pw.setPlaceholderText(u'비밀번호')
        self.input_pw.setFont(self.font)
        self.input_pw.setTextMargins(33, 0, 4, 1)
        self.input_pw.setEchoMode(QLineEdit.Password)
        self.input_pw.setStyleSheet("border-radius:2px;\n"
                                    "border: 1.4px inset gray;\n"
                                    "background-color: WhiteSmoke")
        self.login_gb_layout.addWidget(self.input_pw)

        # ID, PW 입력 이미지 관련
        self.image_user = QLabel(self.input_id)
        self.image_user.setPixmap(QPixmap('image/user.png').scaled(24, 24, Qt.KeepAspectRatioByExpanding,
                                                                     Qt.SmoothTransformation))
        self.image_user.setMargin(2)

        self.image_pw = QLabel(self.input_pw)
        self.image_pw.setPixmap(QPixmap('image/password.png').scaled(22, 22, Qt.KeepAspectRatioByExpanding,
                                                                       Qt.SmoothTransformation))
        self.image_pw.setMargin(3)

        # 로그인 버튼
        self.login_button = QPushButton()
        self.login_button.setFont(self.font)
        self.login_button.setText(u'로그인')

        self.login_button.setMinimumSize(33, 33)
        self.login_gb_layout.addWidget(self.login_button)
        self.login_button.clicked.connect(self.on_login_button_clicked)

        self.login_button.setStyleSheet("background-color: #1565C0;\n"
                                        "border-radius:2px;\n"
                                        "font: 12pt;\n"
                                        "font-weight: 900;\n"
                                        "border: 1.6px outset #1B4F72;\n"
                                        "color: White;")

        self.bottom_gb = QGroupBox()
        self.bottom_box_layout = QHBoxLayout(self.bottom_gb)
        self.bottom_gb.setObjectName("bottom_gb")
        self.login_gb_layout.addWidget(self.bottom_gb)

        # 아이디 저장 체크박스
        self.check_save_id = QCheckBox("아이디 저장")
        self.check_save_id.setFont(self.font)
        self.check_save_id.setStyleSheet('color: CornFlowerBlue;')

        is_remember_me_checked = self.get_remember_me_from_registry()
        self.check_save_id.setChecked(is_remember_me_checked)

        self.bottom_box_layout.addWidget(self.check_save_id)

        # 회원가입 버튼
        self.signup = QPushButton('회원가입')
        self.signup.setCursor(Qt.PointingHandCursor)
        signup_stylesheet = """
        QPushButton {
            font-family: "Malgun Gothic";
            color: #333;
            border: 0px;
            }
        QPushButton::hover {
            font-weight: bold;
            text-decoration: underline;
            }
        """
        self.signup.setStyleSheet(signup_stylesheet)
        self.signup.clicked.connect(self.show_member_join_window)

        self.bottom_box_layout.addWidget(self.signup)
        self.login_gb_layout.setAlignment(Qt.AlignCenter)

        # 비밀번호 변경 버튼
        password_find_btn = QPushButton('비밀번호 변경')
        password_find_btn.setCursor(Qt.PointingHandCursor)
        password_find_btn.setStyleSheet(signup_stylesheet)
        password_find_btn.clicked.connect(self.show_password_find_window)

        self.bottom_box_layout.addWidget(password_find_btn)

    def showEvent(self, event):
        self.showNormal()

    def show_member_join_window(self):
        """회원가입 양식 윈도우를 보여준다."""
        from ui.member_join_window import MemberJoinWindow
        join_win = MemberJoinWindow(parent=self)
        join_win.exec_()

    def show_password_find_window(self):
        """비밀번호 찾기 윈도우를 보여준다."""
        from ui.password_find_window import PasswordFindWindow
        win = PasswordFindWindow(parent=self)
        win.exec_()

    def on_login_button_clicked(self):
        """로그인 버튼을 클릭했을 때"""
        self.check_db_user()

    @staticmethod
    def get_remember_me_from_registry():
        """레지스트리에서 remember_me 값을 가져온다."""

        reg = Registry('Login')
        if reg.exists('remember_me'):
            return reg.get('remember_me') == 1
        return False

    def check_db_user(self):
        """입력한 아이디 패스워드가 데이터베이스에 정보와 일치하는지 확인한다."""

        self.login_success = False
        input_email_addr = self.input_id.text()
        input_pw = self.input_pw.text()

        conn = get_con_smart_maker()
        curs = conn.cursor()

        curs.execute(
            'SELECT id, login_id '
            'FROM users '
            'WHERE email_address=%s '
            'AND password=SHA2(%s, 256)',
            (input_email_addr, input_pw)
        )
        results = curs.fetchall()
        if results:
            """
             로그인이 성공하면 connect_net_drives라는 메소드를 실행한다.
            connect_net_drives 메소드에는 해당 사용자의 네트워크 드라이브 정보를 알아와
            연결해주는 역할을 한다.
            """

            self.email_address = input_email_addr
            self.user_id = results[0][0]
            drive_connect(self.email_address)

            self.login_success = True

            self.save_id_to_registry()

            # if self.check_save_id.isChecked():

            self.accept()
            return
        else:

            self.login_id = None

            self.match_pw_mb = QMessageBox()
            self.match_pw_mb.setMinimumSize(200, 30)
            self.match_pw_mb.setText(u'입력하신 정보를 다시 한번 확인하여 주시길 바랍니다.')
            self.match_pw_mb.setWindowTitle(u'!')
            self.match_pw_mb.setFont(self.font)
            self.match_pw_mb.exec_()


class Command(object):
    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None

    def run(self, timeout):
        def target():
            self.process = subprocess.Popen(self.cmd, shell=True)
            self.process.communicate()

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            # 쓰레드가 timeout= 이상 살아있으면 종료
            self.process.terminate()
            thread.join()

        # 네트워크 드라이브 연결이 되면 리턴코드를 0으로 반환한다.
        # 네트워크 드라이브 연결이 안되면 리턴코드를 1로 반환한다.
        #self.process.returncode

