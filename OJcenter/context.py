import configparser
import platform
import sys
from concurrent.futures import ThreadPoolExecutor

_cf = configparser.ConfigParser()
_host = 'localhost'
_executor = ThreadPoolExecutor(max_workers=10)
if platform.system() == 'Windows':
    _host = '202.4.155.97'
    with open('E:\\other_project\\buct-oj\\OJcenter-new\\OJcenter\\Tool\\config.ini', 'r', encoding='utf-8') as f:
        _cf.read_file(f)
elif platform.system() == 'Linux':
    _cf.read(sys.path[0] + "/OJcenter/Tool/config.ini")


def getConfigValue(section, key):
    return _cf.get(section, key)

def getAllKeys(section):
    return _cf.options(section)

def getHost():
    return _host

def executor():
    return _executor
