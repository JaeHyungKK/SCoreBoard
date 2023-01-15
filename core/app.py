# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtNetwork import *


class QtSingleApplication(QApplication):

    message_received = Signal(str)

    def __init__(self, uuid, *argv):
        super(QtSingleApplication, self).__init__(*argv)
        self.uuid = uuid
        self._activation_window = None
        self._activate_on_message = False

        self.out_socket = QLocalSocket()
        self.out_socket.connectToServer(self.uuid)
        self._running = self.out_socket.waitForConnected()

        if self._running:
            self.out_stream = QTextStream(self.out_socket)
            self.out_stream.setCodec('UTF-8')
        else:
            self.out_socket = None
            self.out_stream = None
            self.in_socket = None
            self.in_stream = None
            self.server = QLocalServer()
            self.server.listen(self.uuid)
            self.server.newConnection.connect(self._on_new_connection)

    def is_running(self):
        return self._running

    def uuid(self):
        return self.uuid

    def activate_window(self):
        if not self._activation_window:
            return
        self._activation_window

    def set_activate_window(self, activation_window, activate_on_message = True):
        self._activation_window = activation_window
        self._activate_on_message = activate_on_message

    def activate_window(self):
        if not self._activation_window:
            return
        self._activation_window.show()

    def send_message(self, msg):
        if not self.out_stream:
            return False
        self.out_stream << msg << '\n'
        self.out_stream.flush()
        return self.out_socket.waitForBytesWritten()

    def _on_new_connection(self):
        if self.in_socket:
            self.in_socket.readyRead.disconnect(self._on_ready_read)
        self.in_socket = self.server.nextPendingConnection()
        if not self.in_socket:
            return
        self.in_stream = QTextStream(self.in_socket)
        self.in_stream.setCodec('UTF-8')
        self.in_socket.readyRead.connect(self._on_ready_read)
        if self._activate_on_message:
            self.activate_window()

    def _on_ready_read(self):
        while True:
            msg = self.in_stream.readLine()
            if not msg:
                break
            self.message_received.emit(msg)
