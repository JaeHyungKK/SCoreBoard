# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
# from resource_rc import *
import sys
import core.db


class PasswordFindWindow(QDialog):

    def __init__(self, parent=None):
        super(PasswordFindWindow, self).__init__(parent)
        self.setObjectName('password_find_window')
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

        title = QLabel('비밀번호 변경')
        title.setFont(QFont('Malgun Gothic', 20, 80))

        desc = QLabel('새로운 비밀번호로 변경할 수 있습니다.\n시스템 관리자에게서 미리 비밀키를 부여 받은 후 진행하세요.')
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
        self.name_field.setFixedWidth(200)

        self.email_address_field = QLineEdit()
        self.email_address_field.setFixedWidth(100)

        self.account_help = QLabel()

        self.password_field1 = QLineEdit()
        self.password_field1.setEchoMode(QLineEdit.Password)

        self.password_field2 = QLineEdit()
        self.password_field2.setEchoMode(QLineEdit.Password)

        self.key_field = QLineEdit()
        self.key_field.setFixedWidth(100)

        submit_btn = QPushButton('작성완료')
        submit_btn.setFixedHeight(30)
        submit_btn.setCursor(Qt.PointingHandCursor)
        submit_btn.clicked.connect(self.submit)

        self.main_form.addRow('성명', self.name_field)
        self.main_form.addRow('이메일 주소 (아이디)', self.email_address_field)
        self.main_form.addRow('변경할 비밀번호', self.password_field1)
        self.main_form.addRow('비밀번호 확인', self.password_field2)
        self.main_form.addRow('비밀키 입력', self.key_field)
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
            QMessageBox.critical(self, '아이디 오류', '아이디를 작성해 주세요.')
            self.email_address_field.setFocus()
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

        secret_key = self.key_field.text()
        if not secret_key:
            QMessageBox.critical(self, '비밀키 오류', '시스템 관리자에게서 부여받은 비밀키를 입력해 주세요.')
            self.key_field.clear()
            self.key_field.setFocus()
            return

        conn = core.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT email_address FROM users WHERE email_address=%s AND name=%s AND secret_key=%s',
            (email_address, name, secret_key),
        )
        result = cursor.fetchone()
        if not result:
            QMessageBox.critical(self, '사용자 오류', '입력한 정보의 사용자는 찾을 수 없습니다. 비밀번호를 변경할 수 없습니다.')
            return

        result = cursor.execute(
            'UPDATE users SET password=PASSWORD(%s), secret_key=NULL '
            'WHERE email_address=%s AND name=%s AND secret_key=%s',
            (password1, email_address, name, secret_key),
        )
        if result == 1:
            conn.commit()
            QMessageBox.information(self, '비밀번호 변경 완료', '원하는 비밀번호로 변경이 완료되었습니다. 변경된 비밀번호를 이용하여 로그인 해주세요.')
            self.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    win = PasswordFindWindow()
    win.show()

    sys.exit(app.exec_())







