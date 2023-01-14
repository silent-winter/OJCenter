import os.path
import platform

import socket

import threading
import _thread
import configparser
import sys
import time
from OJcenter.Tool import redisTool, permanentTool
from OJcenter.Tool import dockerTool
import requests, json

create_wait_times = 20


def _init():
    global _orderDict
    _orderDict = {}
    global _occupiedPort
    _occupiedPort = [None]
    global _createdPort
    _createdPort = []


cleanOccupiedMutex = threading.Lock()
createNewDockerMutex = threading.Lock()


def getOrder(item):
    global _orderDict
    try:
        if item in _orderDict:
            return _orderDict[item]
    except KeyError:
        return -1


def getConfiguration():
    path = sys.path[0] + "/OJcenter/Tool/config.ini"
    cf = configparser.ConfigParser()
    cf.read(path)
    return cf


def judgeSpace():
    global _orderDict
    global _occupiedPort
    global _createdPort
    if len(_occupiedPort) > 0 and _occupiedPort[0] == None:
        return False
    cf = getConfiguration()
    maxuser = int(cf.get("portconfig", "maxuser"))
    if len(_orderDict) > 0 and len(_createdPort) > 0 and len(_occupiedPort) < maxuser:
        return True
    else:
        return False


def refreshDict():
    global _orderDict
    while True:
        try:
            orderList = redisTool.getOrdeList()
            orderDictTemp = {}
            for index in range(len(orderList)):
                orderDictTemp[orderList[index]] = index + 1
            _orderDict = orderDictTemp

            # 把排队中的人划拨到已用人群
            if len(orderList) > 0:
                if judgeSpace():
                    targetUser, targetPort = redisTool.popUser()
        except Exception as re:
            print(re)
        time.sleep(0.1)


def cleanOccupied():
    global _occupiedPort
    while True:
        cleanOccupiedMutex.acquire()

        try:
            _occupiedPort = redisTool.checkToken()
        except Exception as re:
            print(re)

        cleanOccupiedMutex.release()
        time.sleep(5)


# def getOnePort():
#     global _occupiedPort
#     cf = getConfiguration()
#     # startport = int(cf.get("portconfig", "startport"))
#     # endport = int(cf.get("portconfig", "endport"))
#
#     cleanOccupiedMutex.acquire()
#     port = -1
#     for index in range(sys.maxsize):
#         if index >= startport and index <= endport:
#             if index not in _occupiedPort:
#                 if not IsOpen(index):
#                     _occupiedPort.append(index)
#                     port = index
#                     break
#         if index > endport:
#             break
#     cleanOccupiedMutex.release()
#     return port

def getOneContainer():
    global _createdPort
    global _occupiedPort
    cleanOccupiedMutex.acquire()
    createNewDockerMutex.acquire()
    targetPort = -1
    if len(_createdPort) > 0:
        targetPort = _createdPort[0]
        _createdPort.remove(targetPort)
        _occupiedPort.append(targetPort)
    createNewDockerMutex.release()
    cleanOccupiedMutex.release()
    return targetPort


def IsOpen(port, ip="127.0.0.1"):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        # 利用shutdown()函数使socket双向数据传输变为单向数据传输。shutdown()需要一个单独的参数，
        # 该参数表示了如何关闭socket。具体为：0表示禁止将来读；1表示禁止将来写；2表示禁止将来读和写。
        print('%d is open' % port)
        return True
    except Exception as e:
        print('%d is down' % port)
        return False


def refreshOrder():
    try:
        _thread.start_new_thread(cleanOccupied, ())
        _thread.start_new_thread(refreshDict, ())
    except:
        print("Error: 无法启动线程")


def login(username, password):
    baseurl = "127.0.0.1:2336"
    try:
        req = requests.get("http://" + baseurl + "/loginremote.php?username={}&password={}".format(username, password),
                           timeout=5)
    except:
        return False
    res = json.loads(req.text)
    if "statu" in res and res['statu'] == 200 and "PHPSESSID" in dict(req.cookies):
        return dict(req.cookies)
    return False


def initCreatedDockerPort():
    global _createdPort

    createNewDockerMutex.acquire()
    cf = getConfiguration()
    startport = int(cf.get("portconfig", "startport"))
    endport = int(cf.get("portconfig", "endport"))
    for index in range(sys.maxsize):
        if index >= startport and index <= endport:
            if dockerTool.dockerExist(index):
                _createdPort.append(index)
                print(index, "初始化存在")
        if index > endport:
            break

    portList = redisTool.getPortList()
    for item in portList:
        if item in _createdPort:
            _createdPort.remove(item)
    createNewDockerMutex.release()


def refreshCreatedPort():
    try:
        _init()
        initCreatedDockerPort()
        _thread.start_new_thread(refreshCreatedDockerPort, ())
    except:
        print("Error: 无法启动线程")


def waitUntilFinished(targetPort):
    for i in range(create_wait_times):
        try:
            url = 'http://127.0.0.1:' + str(targetPort)
            r = requests.get(url, timeout=5)
            code = r.status_code
            if code == 200:
                return True
        except:
            time.sleep(5)
    return False


def refreshCreatedDockerPort():
    global _createdPort
    while True:
        try:
            cf = getConfiguration()
            startport = int(cf.get("portconfig", "startport"))
            endport = int(cf.get("portconfig", "endport"))
            if endport > startport:
                for index in range(sys.maxsize):
                    if index >= startport and index <= endport:
                        if not dockerTool.dockerExist(index):
                            if not IsOpen(index):
                                targetPort = dockerTool.createContainerWait(index)
                                if targetPort != -1:
                                    waitUntilFinished(targetPort)
                                    createNewDockerMutex.acquire()

                                    _createdPort.append(targetPort)

                                    createNewDockerMutex.release()
                    if index > endport:
                        break
        except Exception as e:
            print(e)
        time.sleep(1)


if __name__ == '__main__':
    IsOpen(80)


def getPHPUserName(PHPSESSID):
    sessionPath = os.path.join("/var/lib/php/sessions/", "sess_" + PHPSESSID)
    if os.path.exists(sessionPath):
        with open(sessionPath) as f:
            content = f.read()
        contentList = content.split(";")
        for item in contentList:
            if item.startswith("BUCTOJ_user_id"):
                userName = item.split("\"")[1]
                return userName
        return None
    else:
        return None


def checkLogin(request):
    return "appmlk"
    # if platform.system() == 'Windows':
    #     return "appmlk"
    # elif(platform.system() == 'Linux'):
    #     if "PHPSESSID" not in request.COOKIES:
    #         return None
    #     PHPSESSID = request.COOKIES["PHPSESSID"]
    #     if PHPSESSID != None:
    #         username = getPHPUserName(PHPSESSID)
    #         return username
    #     else:
    #         return None


def checkContestVerify(targetUser):
    return None


def entercontest(username, contestid):
    targetPort = redisTool.getPort(username)
    targetPath = permanentTool.cleanPermanentPath(username)
    dockerTool.backupPermanentPath(targetPort, targetPath)
    return None
