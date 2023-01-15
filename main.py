# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import sys
import os

from ui_login import LoginWindow
from ui_logout import LogoutWindow
from ui_login_status_win import LoginStatusWindow
# from settings import SettingsWindow
from core.app import QtSingleApplication
from core.db import *
from core.sys_config import *
from core.reg import Registry

import subprocess
from requests import get


class Scoreboard(QMainWindow):

    # def __init__(self, *args, **kwargs):
    #     super(Scoreboard, self).__init__(*args, **kwargs)
    def __init__(self):
        QMainWindow.__init__(self)
        # 이 변수는 로그인 되어있는지 여부를 판단하기 위해서
        # 만들어 놓은 변수이다.
        # 하지만, 이 변수를 이 프로그램에서
        # 직접적으로 읽어서 쓰지 않도록 주의한다.
        # 반드시 self.check_login()이라는 함수를 이용하여,
        # 로그인 여부를 판단하도록 한다.
        self.__logged = False

        # 이 변수는 로그인 창이나 프로필 창이 떠 있는지 아닌지
        # 판단하기 위해서 만들어 놓은 변수이다.
        self.__displayed = False
        self.__admin_displayed = False
        self.__settings_displayed = False
        self.__status_displayed = False
        self.__update_displayed = False

        self.tray = QSystemTrayIcon(self)
        self.init_tray_icon()

        # 트레이 아이콘에 마우스 커서를 올려놓으면 보여줄 문구를 지정한다.
        self.tray.setToolTip("SCOREBOARD")

        # 트레이 메뉴를 생성한다.
        self.create_context_menu()
        # 트레이 아이콘에 마우스 액션이 일어나면 실행될 메소드를 지정한다.
        self.tray.activated.connect(self.icon_activated)

        # 원격 종료 메세지 박스
        self.remote_close_mb = QMessageBox()
        self.remote_close_mb.setMinimumSize(200, 30)
        self.remote_close_mb.setText(u'원격지에서 이 자리를 로그아웃 하였습니다.')
        self.remote_close_mb.setWindowTitle(u'!')

        self.hostname = None
        self.lan_ip = None
        self.wan_ip = None

    def hiding(self):
        self.show_login_tray_message()

    def exit(self):
        sys.exit(0)

    def show(self):
        """로그인 여부에 따라 로그인 윈도우를 보여줄지 메인 윈도우를 보여줄지 결정한다."""

        if self.__logged:
            self.show_profile_window()
        else:
            self.show_login_form()

    def show_login_tray_message(self):
        """ 로그인이 되면 시스템 트레이 메세지를 띄워준다."""

        self.tray.setVisible(True)
        icon = QIcon('C:/mv/laad/image/scoreboard_16.png')
        self.tray.showMessage(
            u'Scoreboard',
            u'로그인이 되어 시스템 트레이로 이동합니다.',
            icon,
            msec=100,
        )

    def show_logout_tray_message(self):
        """ 로그아웃이 되면 시스템 트레이 메세지를 띄워준다."""
        self.tray.setVisible(True)
        icon = QIcon('C:/mv/laad/image/scoreboard_16_off.png')
        self.tray.showMessage(
            u'Scoreboard',
            u'로그아웃 되었습니다.',
            icon,
            2000,
        )

    def create_context_menu(self):

        self.menu = QMenu()

        # 로그인 로그아웃 될때 setContextMenu 를 새로 불러옴
        # 로그인이 되었을 경우 로그아웃, 프로그램 종료가 보이고
        # 로그아웃이 되었을 경우 로그인, 프로그램 종료가 보임
        login_action = QAction('로그인', self)
        login_action.setIcon(QIcon('image/scoreboard_16_off.png'))
        logout_action = QAction('로그아웃', self)
        logout_action.setIcon(QIcon('image/scoreboard_16.png'))
        admin_mode_action = QAction('관리자 설정', self)
        admin_mode_action.setIcon(QIcon('image/admin.png'))
        login_status_action = QAction('로그인 현황', self)
        login_status_action.setIcon(QIcon('image/login_status'))
        update_check_action = QAction('업데이트 확인', self)
        update_check_action.setIcon(QIcon('image/update1-1.png'))
        quit_action = QAction('프로그램 종료', self)
        quit_action.setIcon(QIcon('C:image/quit.png'))

        # 로그인 함수의 값이 참이면 마우스 우클릭 했을 경우
        # 로그아웃이 나오게 하고 거짓이면 로그인이 나오게
        if self.check_login():
            self.menu.addAction(logout_action)
            self.menu.addAction(admin_mode_action)
            self.menu.addAction(login_status_action)
        else:
            self.menu.addAction(login_action)

        self.menu.addSeparator()
        self.menu.addAction(update_check_action)
        self.menu.addSeparator()
        self.menu.addAction(quit_action)

        login_action.triggered.connect(self.show_login_form)
        logout_action.triggered.connect(self.process_logout)
        admin_mode_action.triggered.connect(self.show_admin_login_window)
        login_status_action.triggered.connect(self.show_login_status_window)
        update_check_action.triggered.connect(self.check_update)
        quit_action.triggered.connect(self.quit_application)

        self.tray.setContextMenu(self.menu)
        self.tray.show()

    @staticmethod
    def disconnect_all_net_drives():
        """이 함수 하나로 로그아웃 혹은 프로그램을 종료할 경우
        모든 네트워크 드라이브와의 연결을 종료한다."""

        cmd = u'net use /delete * /y'
        subprocess.call(cmd, shell=True)

    def check_update(self):
        """새로운 업데이트가 있는지 확인한다."""
        import updater
        latest_version = updater.check_latest_version()

        reg = Registry()
        installed_version = reg.get('installed_version')

        if installed_version != latest_version:
            if not self.__update_displayed:
                self.__update_displayed = True
                res = QMessageBox.information(
                    None,
                    '업데이트 필요',
                    '최신 업데이트가 있습니다.\n새로운 버전으로 업데이트 할까요?\n\n{}'.format(latest_version),
                    (QMessageBox.Ok | QMessageBox.Cancel),
                )
                if res == QMessageBox.Ok:
                    self.disconnect_all_net_drives()
                    win = UpdaterWindow()
                    win.exec_()
                    sys.exit(0)
                self.__update_displayed = False
        else:
            if not self.__update_displayed:
                self.__update_displayed = True
                QMessageBox.information(
                    None,
                    '최신버전',
                    '이미 최신 버전의 업데이트가 적용되어 있습니다.',
                    QMessageBox.Ok,
                )
                self.__update_displayed = False
        return

    def show_login_form(self):
        """사용자가 로그인을 하기 위해 로그인 폼을 띄어준다."""

        if not self.__displayed:
            win = LoginWindow()
            self.__displayed = True
            result = win.exec_()

            # 로그인 창이 대기상태일 때
            self.__displayed = False
            if result:
                self.user_id = win.user_id
                self.process_login()

    def show_profile_window(self):
        """프로필 윈도우를 띄워준다."""

        if not self.__displayed:
            win = LogoutWindow(user_id=self.user_id)
            self.__displayed = True
            result = win.exec_()
            self.__displayed = False
            if result:
                self.process_logout()

    def show_login_status_window(self):
        """원격 종료 하면 로그아웃을 진행하고 로그인 상태 윈도우를 띄워준다."""

        # if not self.is_alive():
        #     self.process_logout()
        #     return
        if not self.__status_displayed:
            win = LoginStatusWindow(user_id=self.user_id)
            self.__status_displayed = True
            result = win.exec_()
            # 로그인 창이 대기상태일 때
            self.__status_displayed = False
            if not result:
                return

    def is_alive(self):
        """
        db 테이블에 가서 현재 자리가 인증 받은 자리인지 확인하고 그 결과값을 반환한다.
        """
        conn = get_con_smart_maker()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM alives WHERE private_ip=%s AND public_ip=%s',
            (self.lan_ip, self.wan_ip),
        )
        return cursor.fetchone() is not None

    def show_admin_login_window(self):
        # if not self.is_alive():
        #     self.remote_close_mb.exec_()
        #     self.process_logout()
        #     return

        if not self.__admin_displayed:
            adminloginwin = AdminLoginWindow()
            self.__admin_displayed = True
            result = adminloginwin.exec_()
            self.__admin_displayed = False
            if not result:
                return
    #         settingswin = SettingsWindow()
    #         self.__admin_displayed = True
    #         self.__settings_displayed = True
    #         settingswin.exec_()
    #         self.__admin_displayed = False
    #         self.__settings_displayed = False
    #
    # def show_settings_window(self):
    #     settings = SettingsWindow()
    #     settings.exec_()

    def init_tray_icon(self):
        """로그인 상태에 따라 트레이 아이콘의 아이콘을 로그인용 로그아웃용 아이콘으로 변경해준다."""
        if self.__logged:
            self.tray.setIcon(QIcon('image/scoreboard_16.png'))
        else:
            self.tray.setIcon(QIcon('image/scoreboard_16_off.png'))

    def process_login(self):
        """로그인을 진행한다."""
        self.__logged = True

        self.create_context_menu()
        self.init_tray_icon()
        self.show_login_tray_message()
        # self.get_ip_address()

    def process_logout(self):
        """로그아웃을 진행한다."""
        self.__logged = False
        self.create_context_menu()
        self.init_tray_icon()
        self.disconnect_all_net_drives()
        # self.delete_alives_ip()
        self.show_logout_tray_message()
        self.show_login_form()

    def check_login(self):
        """현재 로그인이 되어있는 상태인지 아닌지 알려준다."""
        return self.__logged

    def quit_application(self):
        """ 시스템트레이에서 프로그램 종료 버튼을 누르면 네트워크 드라이브
        연결을 끊고 프로그램을 종료한다. """

        if self.check_login():
            res = QMessageBox.information(
                None,
                '프로그램 종료',
                ' 프로그램을 종료하면 모든 네트워크 드라이브 \n 연결이 해제됩니다. 진행하시겠습니까?',
                (QMessageBox.Ok | QMessageBox.Cancel),
            )
            if res == QMessageBox.Ok:
                self.disconnect_all_net_drives()
                # self.delete_alives_ip()
                sys.exit(0)
        else:
            sys.exit(0)

    def icon_activated(self, reason):
        """트레이 아이콘 더블클릭시 로그인이 되어있으면 프로필 윈도우를
        로그아웃이 되어있으면 로그인 윈도우를 띄워준다."""
        if reason == QSystemTrayIcon.DoubleClick:

            if self.check_login():
                # if not self.is_alive():
                #     self.remote_close_mb.exec_()
                #     self.process_logout()
                #     return

                # 로그인이 되어있을 때
                # 프로필 윈도우를 띄어준다.
                self.show_profile_window()
            else:
                self.show_login_form()

    def get_ip_address(self):
        """아이피를 얻는다."""
        import socket
        self.hostname = socket.gethostname()
        self.lan_ip = socket.gethostbyname(socket.getfqdn())
        self.wan_ip = get('https://api.ipify.org').text
        self.save_alives_ip()

    def delete_alives_ip(self):
        """접속여부를 판단하기 위해 로그아웃이 되면 아이피 정보를 삭제한다."""
        conn = get_con_smart_maker()
        curs = conn.cursor()
        curs.execute(
            'DELETE FROM alives '
            'WHERE hostname=%s AND private_ip=%s AND public_ip=%s',
            (self.hostname, self.lan_ip, self.wan_ip),
        )
        conn.commit()

    def save_alives_ip(self):
        """접속 여부를 판단하기 위해 로그인이 되면 아이피 정보를 추가한다."""
        if self.user_id is None:
           return
        conn = get_con_smart_maker()
        curs = conn.cursor()
        curs.execute(
            'DELETE FROM alives '
            'WHERE hostname=%s AND private_ip=%s AND public_ip=%s',
            (self.hostname, self.lan_ip, self.wan_ip),
        )

        curs.execute(
            'insert into alives (hostname, private_ip, public_ip, score_user_account) '
            'values (%s, %s, %s, %s)',
            (self.hostname, self.lan_ip, self.wan_ip, self.user_id),
        )
        conn.commit()


class AdminLoginWindow(QDialog):
    def __init__(self, *args, **kwargs):
        super(AdminLoginWindow, self).__init__(*args, **kwargs)
        self.setup_ui()

    def setup_ui(self):

        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(QIcon('image/scoreboard_16.png'))
        self.setFixedSize(270, 140)
        self.main_layout = QVBoxLayout(self)
        self.font = QFont()
        self.font.setFamily("Malgun Gothic")
        self.font.setStyleStrategy(QFont.PreferQuality)
        self.font.setPointSize(9)

        self.admin_login_gb = QGroupBox()
        self.admin_login_gb_Layout = QVBoxLayout(self.admin_login_gb)
        self.admin_login_gb.setObjectName('admin_login_gb')
        self.main_layout.addWidget(self.admin_login_gb)

        self.admin_login_gb.setStyleSheet("background-color: White;")

        self.main_text = QLabel('관리자 비밀번호를 입력하세요')
        self.main_text.setFont(self.font)
        self.main_text.setStyleSheet("font: 12pt;")
        self.main_text.setAlignment(Qt.AlignCenter)

        self.input_pw = QLineEdit()
        self.input_pw.setMinimumSize(32, 30)
        self.input_pw.setFont(self.font)
        self.input_pw.setFocus()
        self.input_pw.setTextMargins(33, 0, 4, 1)
        self.input_pw.setStyleSheet("border-radius:2px;\n"
                                    "border: 1.4px inset gray;\n"
                                    "background-color: WhiteSmoke;")
        self.input_pw.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton()
        self.login_button.setFont(self.font)
        self.login_button.setText('로그인')
        self.login_button.setMinimumSize(32, 30)
        self.login_button.setStyleSheet("background-color: #1565C0;\n"
                                        "border-radius:2px;\n"
                                        "font: 12pt;\n"
                                        "font-weight: 900;\n"
                                        "border: 1.6px outset #1B4F72;\n"
                                        "color: White;")
        self.login_button.clicked.connect(self.check_admin_password)

        self.admin_login_gb_Layout.addWidget(self.main_text)
        self.admin_login_gb_Layout.addWidget(self.input_pw)
        self.admin_login_gb_Layout.addWidget(self.login_button)

    def on_login_button_clicked(self):
        self.check_admin_password()

    def check_admin_password(self):
        _admin_id = ''
        conn = get_con_smart_maker()
        curs = conn.cursor()

        curs.execute(
            'SELECT id, password FROM users '
            'WHERE login_id=%s AND password=PASSWORD(%s)',
            (_admin_id, self.input_pw),
        )

        results = curs.fetchone()
        if results:
            self.accept()
            return
        else:
            self.match_pw_mb = QMessageBox()
            self.match_pw_mb.setMinimumSize(200, 30)
            self.match_pw_mb.setText(u'입력하신 정보를 다시 한번 확인하여 주시길 바랍니다.')
            self.match_pw_mb.setWindowTitle(u'!')
            self.match_pw_mb.setFont(self.font)
            self.match_pw_mb.exec_()
            self.input_pw.clear()

import time
import shutil
import ftplib
import zipfile
from datetime import datetime
import logging
import traceback

import core.db
import imp

imp.reload(sys)
# sys.setdefaultencoding('utf-8')


PROCESS_EXECUTABLE = 'scoreboard.exe'


def get_ftp():
    _IPADDR = ''
    _PORT = 32221
    _FTP_ID = ''
    _FTP_PASSWD = ''

    ftp = ftplib.FTP()
    ftp.connect(_IPADDR, _PORT)
    ftp.login(_FTP_ID, _FTP_PASSWD)
    return ftp


def close_ftp(ftp):
    if ftp:
        ftp.close()


def check_latest_version():
    # 업데이트 할 버전 이름 알아오기
    conn = core.db.get_connection('scoreboard')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT major, minor, build FROM version '
        'ORDER BY id DESC '
        'LIMIT 1'
    )
    result = cursor.fetchone()
    if not result:
        return 'v1.0.0'
    major, minor, build = result
    return 'v{}.{:03d}.{}'.format(major, minor, build)


class UpdaterWindow(QDialog):
    """업데이트 윈도우"""
    def __init__(self, install_mode=False, parent=None):
        super(UpdaterWindow, self).__init__(parent)
        self.install_mode = install_mode

        window_layout = QVBoxLayout(self)
        window_layout.setAlignment(Qt.AlignTop)
        window_layout.setContentsMargins(9, 9, 9, 9)

        main_frame = QFrame()
        main_frame.setFrameShape(QFrame.Box)
        main_frame.setFrameShadow(QFrame.Sunken)

        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(30, 30, 30, 30)

        title_layout = QHBoxLayout()

        title_icon = QLabel()
        title_icon.setPixmap(QPixmap('image/scoreboard_16.png'))

        title = QLabel('스코어보드 업데이터')

        title_layout.addWidget(title_icon)
        title_layout.addWidget(title)
        title_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed))

        self.prog = QProgressBar()
        self.prog.setAlignment(Qt.AlignCenter)

        self.text = QLabel()

        main_layout.addLayout(title_layout)
        main_layout.addItem(QSpacerItem(0, 20))
        main_layout.addWidget(self.prog)
        main_layout.addWidget(self.text)

        window_layout.addWidget(main_frame)

        self.setMinimumWidth(500)
        self.setWindowFlags(Qt.FramelessWindowHint)

        ####################################################################################################
        # 업데이트 시작
        ####################################################################################################
        self.thread = UpdateThread(self.install_mode, self)
        self.thread.update_progress.connect(self.set_progress)
        self.thread.update_label.connect(self.set_label)
        self.thread.update_maximum.connect(self.set_maximum)
        self.thread.started.connect(self.start_thread)
        self.thread.finished.connect(self.finish_thread)

        self.thread.start()

    def set_progress(self, progress):
        self.prog.setValue(progress)

    def set_label(self, txt):
        self.text.setText(txt)

    def set_maximum(self, maximum):
        self.prog.setMaximum(maximum)

    def start_thread(self):
        self.prog.setMaximum(1000)

    @staticmethod
    def finish_thread():
        sys.exit(0)


class UpdateThread(QThread):
    """업데이트 쓰레드"""
    update_progress = Signal(int)
    update_maximum = Signal(int)
    update_label = Signal(str)

    def __init__(self, install_mode=False, parent=None):
        super(UpdateThread, self).__init__(parent)
        self.install_mode = install_mode
        self.install_path = None
        self.action = '설치' if install_mode else '업데이트'
        self.prog = 1

    def progress_step(self, value):
        self.prog = self.prog + value
        self.update_progress.emit(self.prog)
        time.sleep(0.001)

    @staticmethod
    def _get_timestamp(modified_time):
        timestamp = datetime.strptime(modified_time, '%Y%m%d%H%M%S')
        timestamp = timestamp.timetuple()
        timestamp = time.mktime(timestamp)
        timestamp = int(timestamp)
        timestamp = timestamp + 60 * 60 * 9
        return timestamp

    def _retrieve_file_callback(self, data):
        self.copied += len(data)
        self.retrieve_file.write(data)
        self.progress_step(1)

    def file_copy_callback(self, data):
        self.progress_step(1)

    def set_install_path(self, path):
        self.install_path = path

    def run(self):
        self.update_label.emit('{} 준비 중...'.format(self.action))

        # 현재 사용자 로그인 정보를 저장한다.
        self.update_label.emit('사용자 정보를 가져오는 중...')

        # 업데이트 할 버전 이름 알아오기
        update_version = check_latest_version()

        # 레지스트리를 위해 인스턴스를 생성한다.
        reg = Registry()

        if not self.install_path:
            # 스코어보드가 설치되어있는 경로를 찾는다. 없으면 실행을 종료한다.
            self.update_label.emit('스코어보드 설치 경로 찾는 중...')
            self.install_path = reg.get('installed_path')

        # 자동 업데이트용 FTP에 연결한다.
        self.update_label.emit('스코어보드 업데이트 서버에 연결하는 중...')
        ftp = get_ftp()

        self.progress_step(10)

        # 다운로드 할 임시폴더를 생성한다.
        self.update_label.emit('{} 파일을 다운로드 할 준비 중...'.format(self.action))

        download_path = os.path.join(os.environ['temp'], 'scoreboard_updater')
        if not os.path.isdir(download_path):
            os.makedirs(download_path)
        ftp.cwd('/files/updater')
        files = [x for x in ftp.nlst() if x.endswith('{}.zip'.format(update_version))]
        if not files:
            return
        update_filename = files[-1]

        self.progress_step(10)

        block_size = 1024 * 256
        file_size = int(ftp.sendcmd('SIZE %s' % update_filename).split()[-1])
        maximum = file_size / block_size * 8
        self.update_maximum.emit(maximum)

        self.update_label.emit('파일 다운로드 중...')

        modified_time = ftp.sendcmd('MDTM %s' % update_filename).split()[1]
        timestamp = self._get_timestamp(modified_time)
        download_file = os.path.join(download_path, update_filename)
        self.retrieve_file = file(download_file, 'wb')
        self.copied = 0
        # 스코어보드 설치파일이 있는 FTP에 들어가 압축파일을 임시 폴더에 다운로드 한다.
        ftp.retrbinary(
            'RETR {}'.format('/files/updater/' + update_filename),
            self._retrieve_file_callback,
            blocksize=block_size,
        )
        self.retrieve_file.close()
        os.utime(download_file, (timestamp, timestamp))
        close_ftp(ftp)

        self.progress_step(10)

        # 임시 폴더에 서브 폴더를 생성하고 압축을 해제한다.
        extract_path = os.path.join(download_path, 'extract')
        if not os.path.isdir(extract_path):
            os.makedirs(extract_path)

        zf = zipfile.ZipFile(download_file, 'r')
        for fn in zf.namelist():
            utf_fn = fn.decode('euc-kr').encode('utf-8')
            self.update_label.emit('압축 해제 중 : {}'.format(utf_fn))
            dst_fn = os.path.join(extract_path, utf_fn)
            src = zf.open(fn)
            dst = file(dst_fn, 'wb')
            while True:
                data = src.read(block_size)
                if not data:
                    break
                dst.write(data)
                self.progress_step(1)
            src.close()
            dst.close()
        zf.close()

        self.progress_step(10)

        # 업데이트 파일들을 설치되어있는 경로에 덮어쓰기 한다.
        if not os.path.isdir(self.install_path):
            os.makedirs(self.install_path)

        for fn in os.listdir(extract_path):
            self.update_label.emit('파일 복사 중 : {}'.format(fn))
            src_fn = os.path.join(extract_path, fn)
            dst_fn = os.path.join(self.install_path, fn)

            fsrc = file(src_fn, 'rb')
            fdst = file(dst_fn, 'wb')
            while True:
                buf = fsrc.read(block_size)
                if not buf:
                    break
                fdst.write(buf)
                self.progress_step(1)
            fsrc.close()
            fdst.close()

        self.progress_step(10)

        # 업데이트 하기 위해 다운로드하고 압축을 푼 폴더를 삭제한다.
        self.update_label.emit('{} 데이터 정리 중...'.format(self.action))
        if os.path.isdir(download_path):
            shutil.rmtree(download_path, ignore_errors=True)

        self.progress_step(10)

        # 업데이터를 종료한다.
        if self.install_mode:
            self.update_label.emit('{} 완료!'.format(self.action))
        else:
            self.update_label.emit('{} 다운로드 완료! 스코어보드 다운로드 시작...'.format(self.action))
        self.update_progress.emit(maximum)

        if not self.install_mode:
            # update.exe 를 실행한다.
            updater_exe_file = os.path.join(self.install_path, 'updater.exe')
            os.startfile(updater_exe_file)

        time.sleep(1)


def install(parent):
    win = UpdaterWindow(install_mode=True, parent=parent)
    win.show()


def is_running_as_admin():
    """관리자 권한으로 실행하는지 확인하는 메소드"""
    import ctypes
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def bypass_uac(cmd):
    """관리자 권한으로 실행하기 위해 레지스트리에 키를 추가해준다."""
    DELEGATE_EXEC_REG_KEY = 'DelegateExecute'
    try:
        reg.set_bypass_admin(DELEGATE_EXEC_REG_KEY, '')
        reg.set_bypass_admin(None, cmd)
    except WindowsError:
        raise


if __name__ == '__main__':

    reg = Registry()

    try:
        reg.del_bypass_admin()
    except WindowsError:
        pass

    FOD_HELPER = r'C:\Windows\System32\fodhelper.exe'

    app_id = '20191212-SCOREBOARD-BA05-4277-8063-82A6DB9245A2'

    # 싱글 애플리케이션 인스턴스 생성
    app = QtSingleApplication(app_id, sys.argv)
    # 같은 UUID를 가지고 있는 프로세스가 이미 존재하면 프로세스 종료
    if app.is_running():
        sys.exit(0)

    # 레지스트리에 입력할땐 띄어쓰기가 있을 경우 ""로 감싸준다.
    # ex) '"Program Files"'
    # os.path 함수를 사용할 땐 ''만 사용한다..
    # ex) 'Program Files'

    # 관리자 권한 프로그램이 아니기 때문에 uac pass 하고 관리자 권한으로 실행한다.
    # if not is_running_as_admin():
    #     try:
    #         cmd = r'"{}\scoreboard.exe"'.format(os.getcwd())
    #         bypass_uac(cmd)
    #         subprocess.call(FOD_HELPER, shell=True)
    #         sys.exit(0)
    #     except WindowsError:
    #         sys.exit(1)

    # 스코어보드용 레지스트리를 초기화한다.
    if not Registry.init():
        sys.exit(10)

    # 시스템 트레이 아이콘을 윈도우 시스템 트레이에 등록한다.
    scoreboard = Scoreboard()
    app.set_activate_window(scoreboard)
    scoreboard.show()

    # 프로그램이 종료되지 않도록 무한 반복한다.
    # 프로그램 종료는 컨텍스트 메뉴에서 종료할 수 있다.
    while True:
        app.exec_()
