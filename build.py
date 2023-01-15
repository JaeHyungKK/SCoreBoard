# -*- coding: utf-8 -*-
from pprint import pprint, pformat
from datetime import datetime
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
# from resource_rc import *
import os
import time
import subprocess
import core.db
import ftplib
import zipfile


class ScoreboardBuildWindow(QDialog):

    def __init__(self, parent=None):
        super(ScoreboardBuildWindow, self).__init__(parent)
        self.setWindowTitle(u'스코어보드 빌드 시스템')
        self.setWindowIcon(QIcon('image/scoreboard_16.png'))

        self.window_layout = QVBoxLayout(self)
        self.window_layout.setAlignment(Qt.AlignTop)

        self.scoreboard_checkbox = QCheckBox(u'스코어보드')
        self.updater_checkbox = QCheckBox(u'업데이터')
        self.installer_checkbox = QCheckBox(u'인스톨러')

        self.main_prog = QProgressBar()
        self.main_prog.setAlignment(Qt.AlignCenter)
        self.main_prog.setFixedHeight(15)

        self.build_btn = QPushButton(u'빌드 시작')
        self.build_btn.setFixedHeight(30)
        self.build_btn.clicked.connect(self.build)

        self.info_field = QTextEdit()
        self.info_field.setReadOnly(True)
        self.info_field.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.window_layout.addWidget(self.scoreboard_checkbox)
        self.window_layout.addWidget(self.updater_checkbox)
        self.window_layout.addWidget(self.installer_checkbox)
        self.window_layout.addWidget(self.main_prog)
        self.window_layout.addWidget(self.build_btn)
        self.window_layout.addWidget(self.info_field)

        self.setMinimumWidth(600)

    def log(self, message):
        self.info_field.insertPlainText(message + '\n')

    def set_progress(self, progress):
        self.main_prog.setValue(progress)

    def set_label(self, txt):
        self.info_field.insertPlainText(txt + '\n')

    def start_thread(self):
        self.main_prog.setMaximum(50)
        self.build_btn.setEnabled(False)

    def finish_thread(self):
        self.main_prog.setValue(self.main_prog.maximum())
        time.sleep(1)
        self.main_prog.reset()
        self.build_btn.setEnabled(True)

    def build(self):
        thread = BuildThread(self)

        if self.scoreboard_checkbox.isChecked():
            thread.scoreboard_build = True
        if self.updater_checkbox.isChecked():
            thread.updater_build = True
        if self.installer_checkbox.isChecked():
            thread.installer_build = True

        thread.update_progress.connect(self.set_progress)
        thread.update_label.connect(self.set_label)
        thread.started.connect(self.start_thread)
        thread.finished.connect(self.finish_thread)
        thread.start()


class BuildThread(QThread):

    update_progress = Signal(int)
    update_label = Signal(str)

    def __init__(self, parent=None):
        super(BuildThread, self).__init__(parent)
        self.scoreboard_build = False
        self.updater_build = False
        self.installer_build = False
        self.prog = 1

    def log(self, message):
        self.prog += 1
        self.update_progress.emit(self.prog)
        self.update_label.emit(message)
        time.sleep(0.001)

    def run(self):
        root_path = os.path.dirname(__file__)

        if self.scoreboard_build:
            dist_path = os.path.join(root_path, 'dist/scoreboard')
            zip_path = os.path.join(root_path, 'dist-zip/scoreboard')
            self.log('dist_path : {}'.format(dist_path))
            self.log('zip_path : {}'.format(zip_path))

            conn = core.db.get_connection('scoreboard')
            self.log('conn : {}'.format(conn))
            cursor = conn.cursor()
            cursor.execute(
                'SELECT major, minor, build FROM version '
                'ORDER BY major, minor, build'
            )
            self.log('query : {}'.format(cursor.statement))
            results = cursor.fetchall()
            if results:
                major, minor, build = results[-1]
            else:
                major, minor, build = 1, 0, 0
            self.log('major : {}'.format(major))
            self.log('minor : {}'.format(minor))
            self.log('build : {}'.format(build))

            new_minor = minor + 1
            self.log('new_minor : {}'.format(new_minor))

            now = datetime.now()
            base_date = datetime(now.year, 1, 1, 0, 0, 0)
            sub = now - base_date
            year_prefix = str(now.year)[2:]
            seconds = str(sub.seconds)
            self.log('seconds : {}'.format(seconds))

            build_number = ''.join([year_prefix, seconds])
            self.log('build_number : {}'.format(build_number))

            new_version_name = 'v{}.{:03d}.{}'.format(major, new_minor, build_number)
            self.log('new_version_name : {}'.format(new_version_name))

            cursor.execute(
                'INSERT INTO version (major, minor, build, maintainer) '
                'VALUES (%s, %s, %s, %s)',
                (major, new_minor, build_number, '시스템매니저')
            )
            conn.commit()
            self.log('commit()')
            # 빌드
            self.log('Build_bat start.')
            build_bat = os.path.join(root_path, 'build_scoreboard.bat')
            self.log('build_bat : {}'.format(build_bat))
            subprocess.call(build_bat, shell=False)
            self.log('Build_bat finished.')

            # 압축하기
            self.log('Compressing files.')
            if not os.path.isdir(zip_path):
                os.makedirs(zip_path)
            zf_name = 'scoreboard_{}.zip'.format(new_version_name)
            zf_file = os.path.join(zip_path, zf_name)
            with zipfile.ZipFile(zf_file, 'w') as zf:
                for path, _, files in os.walk(dist_path):
                    for f in files:
                        if f == zf_name:
                            continue
                        if f == 'zip':
                            continue
                        fullpath = os.path.join(path, f)
                        relpath = os.path.relpath(fullpath, dist_path)
                        zf.write(fullpath, relpath, zipfile.ZIP_DEFLATED)
            self.log('File compressed.')

            # FTP에 전송

            _IPADDR = ''
            _PORT = 32221
            _FTP_ID = ''
            _FTP_PASSWD = ''

            self.log('FTP open.')
            ftp = ftplib.FTP()
            ftp.connect(_IPADDR, _PORT)
            ftp.login(_FTP_ID, _FTP_PASSWD)

            ftp_path = '/files/scoreboard/'
            ftp.cwd(ftp_path)

            # source의 파일 변경 시간을 타임스탬프로 알아낸다.
            modified_time = os.path.getmtime(zf_file)
            modified_time = int(modified_time)
            self.log('modified_time : {}'.format(modified_time))

            # 파일의 정보를 얻는다.
            ftp.storbinary('STOR {}/{}'.format(ftp_path, zf_name), file(zf_file, 'rb'), blocksize=1024 * 256)
            ftp.close()
            self.log('FTP uploaded.')

        if self.updater_build:
            dist_path = os.path.join(root_path, 'dist/updater')
            zip_path = os.path.join(root_path, 'dist-zip/updater')
            self.log('dist_path : {}'.format(dist_path))
            self.log('zip_path : {}'.format(zip_path))

            # 빌드
            self.log('Build_bat start.')
            build_bat = os.path.join(root_path, 'build_updater.bat')
            self.log('build_bat : {}'.format(build_bat))
            subprocess.call(build_bat, shell=False)
            self.log('Build_bat finished.')

            # 압축하기
            self.log('Compressing files.')
            if not os.path.isdir(zip_path):
                os.makedirs(zip_path)
            zf_name = 'updater_{}.zip'.format(new_version_name)
            zf_file = os.path.join(zip_path, zf_name)
            with zipfile.ZipFile(zf_file, 'w') as zf:
                for path, _, files in os.walk(dist_path):
                    for f in files:
                        if f == zf_name:
                            continue
                        if f == 'zip':
                            continue
                        fullpath = os.path.join(path, f)
                        relpath = os.path.relpath(fullpath, dist_path)
                        zf.write(fullpath, relpath, zipfile.ZIP_DEFLATED)
            self.log('File compressed.')

            # FTP에 전송
            self.log('FTP open.')
            ftp = ftplib.FTP()
            ftp.connect(_IPADDR, _PORT)
            ftp.login(_FTP_ID, _FTP_PASSWD)

            ftp_path = '/files/updater/'
            ftp.cwd(ftp_path)

            # source의 파일 변경 시간을 타임스탬프로 알아낸다.
            modified_time = os.path.getmtime(zf_file)
            modified_time = int(modified_time)
            self.log('modified_time : {}'.format(modified_time))

            # 파일의 정보를 얻는다.
            ftp.storbinary('STOR {}/{}'.format(ftp_path, zf_name), file(zf_file, 'rb'), blocksize=1024 * 256)
            ftp.close()
            self.log('FTP uploaded.')

        if self.installer_build:
            # 빌드
            self.log('Build_bat start.')
            build_bat = os.path.join(root_path, 'build_installer.bat')
            self.log('build_bat : {}'.format(build_bat))
            subprocess.call(build_bat, shell=False)
            dist_path = os.path.join(root_path, 'dist-install')
            installer_filename = 'scoreboard_install.exe'
            installer_file = os.path.join(dist_path, installer_filename)
            self.log('installer_file : {}'.format(installer_file))
            self.log('Build_bat finished.')

            # FTP에 전송
            self.log('FTP open.')
            ftp = ftplib.FTP()
            ftp.connect(_IPADDR, _PORT)
            ftp.login(_FTP_ID, _FTP_PASSWD)

            ftp_path = '/files/scoreboard_install'
            ftp.cwd(ftp_path)

            # source의 파일 변경 시간을 타임스탬프로 알아낸다.
            modified_time = os.path.getmtime(installer_file)
            modified_time = int(modified_time)
            self.log('modified_time : {}'.format(modified_time))
            self.log('os.path.isfile(installer_file) : {}'.format(os.path.isfile(installer_file)))

            # 파일의 정보를 얻는다.
            ftp.storbinary('STOR {}/{}'.format(ftp_path, installer_filename), file(installer_file, 'rb'), blocksize=1024 * 256)
            ftp.close()
            self.log('FTP uploaded.')

        self.log('Build completed.')


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)

    build_window = ScoreboardBuildWindow()
    build_window.show()

    sys.exit(app.exec_())
