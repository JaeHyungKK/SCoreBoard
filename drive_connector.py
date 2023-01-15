# -*- coding: utf-8 -*-

import subprocess
from core.db import *


def command(drive_name, private_ip, conn_path, conn_id, passwd):
    # 네트워크 드라이브를 연결하는 함수
    cmd = r'net use {}: \\{}\{} /user:{} {} /persistent:yes'.format(
        drive_name, private_ip, conn_path, conn_id, passwd)
    try:
        subprocess.run(cmd, timeout=1, shell=True)
    except WindowsError:
        pass
    except subprocess.TimeoutExpired:
        pass


def drive_connect(email_address):
    """사용자 이메일로 사용이 등록된 네트워크 드라이브 정보를
    가져와 연결한다. """
    results = connect_net_drives(email_address=email_address)

    for r in results:
        conn_id = r[0]
        drive_name = r[3]
        conn_path = r[4]
        private_ip = r[5]
        passwd = r[6]

        # 네트워크 드라이브를 연결하기 전에 확실하게 하기 위해서 무조건 끊는다.
        cmd = r'net use {}: /delete /y'.format(drive_name)
        try:
            subprocess.run(cmd, timeout=1, shell=True)
        except WindowsError:
            pass
        except subprocess.TimeoutExpired:
            pass

        # 네트워크 드라이브를 연결한다.
        command(drive_name, private_ip, conn_path, conn_id, passwd)


