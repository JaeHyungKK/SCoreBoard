# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from datetime import datetime

# from resource_rc import *

from core.reg import Registry

import os
import sys
import time
import shutil
import ftplib
import zipfile
import logging
import traceback
import subprocess

import core.db

# reload(sys)
# sys.setdefaultencoding('utf-8')


def get_ftp():

    _IPADDR = ''
    _PORT = 32221
    _FTP_ID = ''
    _FTP_PASSWD = ''

    ftp = ftplib.FTP()
    ftp.connect(_IPADDR, 32221)
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
        title_icon.setPixmap(QPixmap(':/image/scoreboard_16.png'))

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

        # 임시 # install.py에 추가 했기 때문에 다음 업데이트 버전에서는 삭제 해야된다.
        # Windows 앱에 scoreboard 바로가기가 실행이 되지 않아
        # 실행이되도록 바로가기 속성 시작 위치에 스코어보드 실행파일 디렉토리 추가
        self.add_app()

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

    def add_app(self):
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")

        dest_dir = r'C:/ProgramData/Microsoft/Windows/Start Menu/Programs/SCoreBoard'
        score_dir = r'C:/Program Files/SCoreBoard'
        score_exe = r'C:/Program Files/SCoreBoard/scoreboard.exe'

        if not os.path.isdir(dest_dir):
            os.mkdir(dest_dir)

        if os.path.isfile(score_exe):
            score_path = os.path.join(dest_dir, 'scoreboard.lnk')
            score_shortcut = shell.CreateShortCut(score_path)
            score_shortcut.Targetpath = score_exe
            score_shortcut.WorkingDirectory = score_dir
            score_shortcut.save()


class UpdateThread(QThread):

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

    def is_running_as_admin(self):
        import ctypes
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def bypass_uac(self, cmd):
        reg = Registry()
        DELEGATE_EXEC_REG_KEY = 'DelegateExecute'
        try:
            reg.set_bypass_admin(DELEGATE_EXEC_REG_KEY, '')
            reg.set_bypass_admin(None, cmd)
        except WindowsError:
            raise

    def run(self):
        self.update_label.emit('{} 준비 중...'.format(self.action))

        # 현재 사용자 로그인 정보를 저장한다.
        self.update_label.emit('사용자 정보를 가져오는 중...')
        user_id = 'gmdirect'

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

        ftp.cwd('/files/scoreboard')
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
            'RETR {}'.format('/files/scoreboard/' + update_filename),
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

        # 레지스트리에 설치경로 정보를 업데이트 한다.
        self.update_label.emit('{} 경로 기록 중...'.format(self.action))
        reg.set('installed_path', self.install_path)

        # 레지스트리에 설치버전 정보를 업데이트 한다.
        self.update_label.emit('{} 버전 기록 중...'.format(self.action))
        reg.set('installed_version', update_version)

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
            self.update_label.emit('{} 완료! 스코어보드 실행 중...'.format(self.action))
        self.update_progress.emit(maximum)

        if not self.install_mode:

            scoreboard_exe_file = os.path.join(self.install_path, 'scoreboard.exe')

            FOD_HELPER = r'C:\Windows\System32\fodhelper.exe'

            # scoreboard.exe 관리자 권한 프로그램이 아니기 때문에
            # 스코어보드를 uac pass 하고 로그인 유지하여 관리자 권한으로 실행한다.
            try:
                self.bypass_uac(scoreboard_exe_file)
                subprocess.call(FOD_HELPER, shell=True)
            except WindowsError:
                sys.exit(1)

        time.sleep(1)


def install(parent):
    win = UpdaterWindow(install_mode=True, parent=parent)
    win.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    updatewin = UpdaterWindow()
    updatewin.show()
    sys.exit(app.exec_())
