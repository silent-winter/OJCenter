import _thread
import logging
import os.path
import socket
import threading
import time

import phpserialize
import redis

import json
import requests

from OJcenter import context
from OJcenter.Tool import redisTool, permanentTool, dockerTool, k8sTool, userTool, messageTool

from channels.layers import get_channel_layer
from channels.exceptions import ChannelFull

create_wait_times = 20
_orderDict = {}
_createdPort = []
_occupiedPort = [None]
_result = []
# 初始化配置文件
_startPort = int(context.getConfigValue("portconfig", "startport"))
_endPort = int(context.getConfigValue("portconfig", "endport"))
_maxUser = int(context.getConfigValue("portconfig", "maxuser"))
_maxNum = int(context.getConfigValue("portconfig", "maxNum"))

def _init():
    pass
    # global _orderDict
    # _orderDict = {}
    # global _occupiedPort
    # _occupiedPort = [None]
    # global _createdPort
    # _createdPort = []
    # global _result
    # _result = []


cleanOccupiedMutex = threading.Lock()
createNewDockerMutex = threading.Lock()


def getOrder(item):
    global _orderDict
    try:
        if item in _orderDict:
            return _orderDict[item]
    except KeyError:
        return -1


# def getConfiguration():
#     path = sys.path[0] + "/OJcenter/Tool/config.ini"
#     cf = configparser.ConfigParser()
#     cf.read(path)
#     return cf


def judgeSpace():
    global _orderDict
    global _occupiedPort
    if len(_occupiedPort) > 0 and _occupiedPort[0] is None:
        return False
    if len(_orderDict) > 0 and len(_occupiedPort) < _maxUser:
        return True
    else:
        return False


def refreshDict():
    global _orderDict
    while True:
        try:
            # 排队学生：[2019040420, 2019040419, ...]
            orderList = redisTool.getOrdeList()
            orderDictTemp = {}
            for index in range(len(orderList)):
                orderDictTemp[orderList[index]] = index + 1
            # {2019040420: 1, 2019040419: 2, ...}
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

# def getOneContainer():
#     global _createdPort
#     global _occupiedPort
#     cleanOccupiedMutex.acquire()
#     createNewDockerMutex.acquire()
#     targetPort = -1
#     if len(_createdPort) > 0:
#         targetPort = _createdPort[0]
#         _createdPort.remove(targetPort)
#         _occupiedPort.append(targetPort)
#     createNewDockerMutex.release()
#     cleanOccupiedMutex.release()
#     return targetPort


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
        # _thread.start_new_thread(createPersistencePod, ())
    except:
        print("Error: 无法启动线程")


def createPersistencePod():
    while True:
        initK8sPod()
        time.sleep(60)


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


# def initCreatedDockerPort():
#     global _createdPort
#
#     createNewDockerMutex.acquire()
#     for index in range(sys.maxsize):
#         if _startPort <= index <= _endPort:
#             if dockerTool.dockerExist(index):
#                 _createdPort.append(index)
#                 print(index, "初始化存在")
#         if index > _endPort:
#             break
#
#     portList = redisTool.getPortList()
#     for item in portList:
#         if item in _createdPort:
#             _createdPort.remove(item)
#     createNewDockerMutex.release()


# 根据配置文件初始化pod
def initK8sPod():
    result = k8sTool.init(_startPort, _endPort)
    logging.info("pods = {} created".format(result))
    for pod in result:
        redisTool.savePod(pod)


def isPermanentPort(port):
    return _startPort <= port <= _endPort


# def refreshCreatedPort():
#     try:
#         _init()
#         initCreatedDockerPort()
#         _thread.start_new_thread(refreshCreatedDockerPort, ())
#     except:
#         print("Error: 无法启动线程")


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


# def refreshCreatedDockerPort():
#     global _createdPort
#     while True:
#         try:
#             if _endPort > _startPort:
#                 for index in range(sys.maxsize):
#                     if _startPort <= index <= _endPort:
#                         if not dockerTool.dockerExist(index):
#                             if not IsOpen(index):
#                                 targetPort = dockerTool.createContainerWait(index)
#                                 if targetPort != -1:
#                                     waitUntilFinished(targetPort)
#                                     createNewDockerMutex.acquire()
#
#                                     _createdPort.append(targetPort)
#
#                                     createNewDockerMutex.release()
#                     if index > _endPort:
#                         break
#         except Exception as e:
#             print(e)
#         time.sleep(1)

def get_session_id(request):
    if "PHPSESSID" not in request.COOKIES:
        return None
    return request.COOKIES["PHPSESSID"]

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

def is_admin(session_id):
    session_file = os.path.join("/var/lib/php/sessions/", "sess_" + session_id)
    if os.path.exists(session_file):
        with open(session_file) as f:
            content = f.read()
        content_list = content.split(";")
        for item in content_list:
            if item.startswith("BUCTOJ_administrator"):
                return item.split("\"")[1] == 'true'
        return False
    else:
        return False


def checkLogin(request):
    if "PHPSESSID" not in request.COOKIES:
        return None
    PHPSESSID = request.COOKIES["PHPSESSID"]
    if PHPSESSID is not None:
        username = getPHPUserName(PHPSESSID)
        return username
    else:
        return None


def checkContestVerify(targetUser):
    return None


def entercontest(username, contestid):
    targetPort = redisTool.getPort(username)
    targetPath = permanentTool.cleanPermanentPath(username)
    dockerTool.backupPermanentPath(targetPort, targetPath)
    return None

def killHighCPUPods():
    try:
        r = redis.Redis(host=context.getHost(), port=6379, decode_responses=True)
        pod_cnt = {}

        while True:

            pod_metrics_list = k8sTool.get_pod_metrics()['items']
            metrics_map = {pod['metadata']['name']: pod['containers'][0]['usage'] for pod in pod_metrics_list}
            
            user_keys = r.keys('UserPort:*')

            for user_key in user_keys:
                username = user_key.split(':')[1]
                port = r.get(user_key)

                pod = k8sTool.getPod(port)
                pod_name = pod.metadata.name
                # memory = str(round(int(metrics_map[pod_name]['memory'][:-2]) / 1024.0, 2)) + 'MB' if pod_name in metrics_map else '暂无数据'
                cpu = round(int(metrics_map[pod_name]['cpu'][:-1]) / 1000000, 2) if pod_name in metrics_map else 0

                if cpu > 380:
                    if pod_name in pod_cnt:
                        pod_cnt[pod_name] += 1
                    else:
                        pod_cnt[pod_name] = 1
                    logging.warning("username={}, podName={} use cpu={}, counter={}".format(username, pod_name, cpu, pod_cnt[pod_name]))
                    if pod_cnt[pod_name] >= 3:
                        redisTool.removeUser(username)
                        del pod_cnt[pod_name]
                        messageTool.websocket_send_message(username, {"type": "kick", "body": {"reason": "您CPU使用率过高，管理员已将您踢出，若要继续使用请重新申请"}})
                else:
                    if pod_name in pod_cnt:
                        del pod_cnt[pod_name]
            time.sleep(20)
    except Exception as e:
        logging.error(e)


def refreshPodsStatus():
    try:
        _thread.start_new_thread(killHighCPUPods, ())
    except:
        print("Error: 无法启动Pods监测线程")
    return

def newUserToken():
    try:
        while True:
            onlineUserList = redisTool.getOnlineUserList()
            logging.info("online users: " + json.dumps(onlineUserList))
            channel_layer = get_channel_layer()

            for user in onlineUserList:
                group_name = 'user_' + user
                cnt = getattr(channel_layer, group_name, 0)
                if cnt != 0:
                    redisTool.queryUser(user)
            
            time.sleep(120)
    except Exception as e:
        print("Token刷新程序报错")
        print(e)


def refreshUserToken():
    try:
        _thread.start_new_thread(newUserToken, ())
    except:
        print("Error: 无法启动Token刷新线程")