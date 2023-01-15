# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
# from resource_rc import *
import sys
import core.db


class MemberJoinWindow(QDialog):
    """회원가입을 할 수 있는 창"""

    def __init__(self, parent=None):
        super(MemberJoinWindow, self).__init__(parent)
        self.setObjectName('member_join_window')
        self.setWindowIcon(QIcon('image/scoreboard_16.png'))
        self.setWindowTitle('ScoreBoard')

        # 윈도우 레이아웃
        self.window_layout = QVBoxLayout(self)
        self.window_layout.setAlignment(Qt.AlignTop)
        self.window_layout.setContentsMargins(0, 0, 0, 0)
        self.window_layout.setSpacing(0)

        # 배너
        banner = QWidget()
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(30, 30, 10, 10)

        title = QLabel('회원가입')
        title.setFont(QFont('Malgun Gothic', 20, 80))

        desc = QLabel('ScoreBoard 소프트웨어 시스템의 멤버가 되려면 아래의 양식대로 내용을 작성해주세요')
        desc.setWordWrap(True)

        banner_layout.addWidget(title)
        banner_layout.addWidget(desc)

        # 메인 레이아웃
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(10)

        # 폼 레이아웃
        self.main_form = QFormLayout()

        self.name_field = QLineEdit()
        self.name_field.setFixedWidth(100)

        self.email_address_field = QLineEdit()
        self.email_address_field.setFixedWidth(200)

        self.account_help = QLabel()

        self.password_field1 = QLineEdit()
        self.password_field1.setEchoMode(QLineEdit.Password)

        self.password_field2 = QLineEdit()
        self.password_field2.setEchoMode(QLineEdit.Password)

        submit_btn = QPushButton('작성완료')
        submit_btn.setFixedHeight(30)
        submit_btn.setCursor(Qt.PointingHandCursor)
        submit_btn.clicked.connect(self.submit)

        self.main_form.addRow('이름', self.name_field)
        self.main_form.addRow('이메일 주소(아이디)', self.email_address_field)
        self.main_form.addRow('비밀번호', self.password_field1)
        self.main_form.addRow('비밀번호 확인', self.password_field2)
        self.main_form.addRow(None, submit_btn)

        # 레이아웃
        self.main_layout.addLayout(self.main_form)
        self.window_layout.addWidget(banner)
        self.window_layout.addLayout(self.main_layout)

        # 윈도우 기본 속성
        self.setFixedSize(self.sizeHint())
        self.setFixedWidth(400)

    def submit(self):
        name = self.name_field.text()
        if not name:
            QMessageBox.critical(self, '이름 오류', '이름을 작성해 주세요.')
            self.name_field.setFocus()
            return

        email_address = self.email_address_field.text()
        if not email_address:
            QMessageBox.critical(self, '이메일 주소 오류', '이메일 주소를 작성해 주세요.')
            self.email_address.setFocus()
            return

        password1 = self.password_field1.text()
        password2 = self.password_field2.text()

        if not password1 or not password2:
            QMessageBox.critical(self, '비밀번호 오류', '비밀번호를 입력해 주세요.')
            self.password_field1.clear()
            self.password_field2.clear()
            self.password_field1.setFocus()
            return

        if password1 != password2:
            QMessageBox.critical(self, '비밀번호 에러', '비밀번호가 서로 일치하지 않습니다.')
            self.password_field1.clear()
            self.password_field2.clear()
            self.password_field1.setFocus()
            return

        conn = core.db.get_con_smart_maker()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT email_address FROM users WHERE email_address=%s AND name=%s',
            (email_address, name),
        )
        result = cursor.fetchone()
        if result:
            QMessageBox.critical(self, '이미 있는 아이디', '이미 등록된 사용자입니다.')
            return

        cursor.execute(
            'INSERT INTO users (email_address, password, name) VALUES (%s, PASSWORD(%s), %s)',
            (email_address, password1, name),
        )
        conn.commit()
        QMessageBox.information(self, '등록 완료', '회원가입 요청이 정상적으로 완료되었습니다. 관리자의 승인을 기다리세요.')
        self.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    win = MemberJoinWindow()
    win.show()

    sys.exit(app.exec_())







