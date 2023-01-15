# -*- coding: utf-8 -*-

import mysql.connector

HOST = u''
PASSWORD = u''


def get_connection(db='scoreboard'):

    conn = None
    if conn is None:
        conn = mysql.connector.connect(
            host=HOST,
            user='root',
            password=PASSWORD,
            db=db,
            charset='utf8'
        )
    return conn


def get_con_smart_maker(db='smart_maker'):

    conn = None

    if conn is None:
        conn = mysql.connector.connect(
            host=HOST,
            user='root',
            password=PASSWORD,
            db=db,
            charset='utf8'
        )
    return conn


def get_user_info(input_search):
    conn = get_con_smart_maker()
    curs = conn.cursor()
    curs.execute(
        'SELECT '
        '   u.id, '
        '   u.team, '
        '   u.nickname, '
        '   u.name, '
        '   u.login_id, '
        '   u.email_address, '
        '   u.ip '
        'FROM users u '
        'WHERE '
        '   u.team LIKE %s or u.nickname LIKE %s OR u.name LIKE %s',
        ("%" + input_search + "%", "%" + input_search + "%", "%" + input_search + "%",)
    )

    result = curs.fetchall()
    conn.close()

    if result is not None:
        return result
    else:
        return


def connect_net_drives(email_address):
    if email_address is None:
        return
    conn = get_con_smart_maker()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT '
        'u.login_id, '
        'u.name, '
        'u.email_address, '
        'n.drive, '
        'n.shared_dir, '
        's.private_ip, '
        'CONVERT(AES_DECRYPT(UNHEX(s.password), SHA2("1234*", 256)) USING UTF8) '
        'FROM connections c '
        'LEFT JOIN netdrive n ON n.id=c.netdrive_id '
        'LEFT JOIN users u ON u.id=c.users_id '
        'LEFT JOIN server s ON s.id=n.server_id '
        'WHERE '
        'email_address=%s',
        (email_address,)
    )
    results = cursor.fetchall()
    return results

