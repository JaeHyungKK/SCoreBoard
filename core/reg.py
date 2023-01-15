# -*- coding: utf-8 -*-
from core.sys_config import *
import winreg as reg


class Registry(object):

    ROOT_PATH = r'Software\SCoreBoard\{}'.format(APP_NAME)

    def __init__(self, sub_path=None):
        if sub_path:
            self.path = r'{}\{}'.format(self.ROOT_PATH, sub_path)
        else:
            self.path = self.ROOT_PATH
        key = reg.ConnectRegistry(None, reg.HKEY_CURRENT_USER)
        reg.CreateKey(key, self.path)

    @classmethod
    def init(cls):
        try:
            reg.CreateKey(reg.HKEY_CURRENT_USER, cls.ROOT_PATH)
            return True
        except WindowsError:
            return False

    def exists(self, name):
        try:
            registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER, self.path, 0, reg.KEY_READ)
            reg.QueryValueEx(registry_key, name)
            return True
        except WindowsError:
            return False

    def get(self, name):
        try:
            registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER, self.path, 0, reg.KEY_READ)
            value, regtype = reg.QueryValueEx(registry_key, name)
            reg.CloseKey(registry_key)
            return value
        except WindowsError:
            return None

    def set(self, name, value):
        try:
            reg.CreateKey(reg.HKEY_CURRENT_USER, self.path)
            registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER, self.path, 0, reg.KEY_WRITE)
            if isinstance(value, (int, float)):
                reg.SetValueEx(registry_key, name, 0, reg.REG_DWORD, value)
            else:
                reg.SetValueEx(registry_key, name, 0, reg.REG_SZ, value)
            reg.CloseKey(registry_key)
            return True
        except WindowsError:
            return False

    def set_bypass_admin(self, key, value):
        path = r'Software\Classes\ms-settings\shell\open\command'
        try:
            reg.CreateKey(reg.HKEY_CURRENT_USER, path)
            registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER, path, 0, reg.KEY_WRITE)
            reg.SetValueEx(registry_key, key, 0, reg.REG_SZ, value)
            reg.CloseKey(registry_key)
        except WindowsError:
            raise

    def del_bypass_admin(self):
        path = r'Software\Classes\ms-settings\shell\open\command'
        try:
            reg.DeleteKey(reg.HKEY_CURRENT_USER, path)
        except WindowsError:
            raise