import configparser
import sys

_cf = configparser.ConfigParser()
_cf.read(sys.path[0] + "/OJcenter/Tool/config.ini")
# with open('E:\\python_project\\OJcenter\\OJcenter\\Tool\\config.ini', 'r', encoding='utf-8') as f:
#     _cf.read_file(f)


def getConfigValue(section, key):
    return _cf.get(section, key)


def getAllKeys(section):
    return _cf.options(section)
