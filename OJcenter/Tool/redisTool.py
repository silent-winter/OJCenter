import platform
import threading
import time
import uuid
import redis  # 导入redis 模块
from OJcenter.Tool import dockerTool, systemTool, permanentTool, k8sTool

ex_time = 15 * 60
# ex_time = 1 * 30
all_time = 3 * 60 * 60
# all_time = 5 * 60
_Str_User_to_Port = "UserPort"
_Str_User_to_Token = "UserToekn"
_Str_Port_to_User = "PortUser"
_Str_Port_Start_Time = "PortStartTime"
_Str_User_File_Save_Mode = "FileSaveMode"

r = redis.Redis(host='localhost', port=6379, decode_responses=True)


# 把用户放进队列
def connectRedis():
    if platform.system() == 'Windows':
        return redis.Redis(host='81.70.8.85', port=6379, decode_responses=True)
    elif platform.system() == 'Linux':
        return redis.Redis(host='localhost', port=6379, decode_responses=True)
    else:
        return redis.Redis(host='localhost', port=6379, decode_responses=True, password="kujiji555")


def checkUserInList(username):
    try:
        # with open(sys.path[0] + "/OJcenter/Tool/userList","r") as f:
        with open("/home/judge/data/5628/userlist.in", "r") as f:
            templist = f.read().splitlines()

        if len(templist[0].strip()) == 0:
            return True

        if username in templist:
            return True
        else:
            return False
    except:
        return True


def insertUser(username):
    # if username!="appmlk":
    #     return "VScode编程平台维护通知：2022/3/30 21:00-2022/3/31 3:00期间，本系统将会升级维护，期间所有用户无法使用。感谢各位老师、同学的理解与支持。"

    if not checkUserInList(username):
        return "本系统当前被用于考试/比赛，而您未被邀请参加，因此暂时无法使用本系统。如有疑问请联系考试/比赛组织者"

    if r.exists(_Str_User_to_Port + username):
        print(username, "已在使用docker")
        return "已经在使用了，不能排队"
    if r.exists('vsUserList'):
        length = r.llen('vsUserList')
        userList = r.lrange('vsUserList', 0, length)
        find = False
        for item in userList:
            if item == username:
                find = True
                break
        if find:
            print(username, "已存在")
            return "已经在队列中了"
        else:
            r.lpush('vsUserList', username)
            return "成功排队"
    else:
        r.lpush('vsUserList', username)
        return "成功排队"


def getOrdeList():
    orderList = []
    if r.exists('vsUserList'):
        length = r.llen('vsUserList')
        userList = r.lrange('vsUserList', 0, length)
        userList.reverse()
        orderList = userList
    return orderList


def createToken():
    return str(uuid.uuid1()).replace("-", "")


# 从队首取出一个用户
# -1：出现错误
# targetUser, targetPort：队首用户名，对应的端口号
def popUser():
    if r.exists('vsUserList'):
        length = r.llen('vsUserList')
        if length > 0:

            # targetPort=dockerTool.createContainer()
            podInfo = k8sTool.select()
            print(podInfo)
            hostIp, targetPort, pvPath = podInfo.ip, podInfo.port, podInfo.pvPath
            if targetPort == -1:
                return -1, -1

            targetUser = r.rpop('vsUserList')
            # 替换为docker代码
            # targetPort = 1000

            targetTokens = createToken()
            r.set(_Str_User_to_Port + targetUser, "%s-%s" % (hostIp, targetPort))
            r.set(_Str_User_to_Token + targetUser, targetTokens)

            r.set(_Str_Port_to_User + str(targetPort), targetUser)
            r.set(_Str_Port_Start_Time + str(targetPort), int(time.time()))

            r.set(targetTokens, targetPort, ex=ex_time)

            if systemTool.checkContestVerify(targetUser):
                r.set(_Str_User_File_Save_Mode + targetUser, 0)
                targetInnerPath = permanentTool.initEmptyFolder()
            else:
                r.set(_Str_User_File_Save_Mode + targetUser, 1)
                targetInnerPath = permanentTool.initUserFolder(targetUser, pvPath)

            # dockerTool.copyPermanentFolder(targetUser, targetPort, targetInnerPath)
            k8sTool.copy_permanent_folder(targetUser, pvPath)

            # r.set(_Str_User_to_Token + targetUser, targetTokens, ex=ex_time)
            return targetUser, targetPort
        else:
            return -1, -1
    else:
        return -1, -1


# 查询用户当前是否正在使用Dokcer
def queryUser(username):
    if r.exists(_Str_User_to_Token + username):
        targetToken = r.get(_Str_User_to_Token + username)
        if r.exists(targetToken):
            r.expire(targetToken, ex_time)
            return True
        else:
            return False
    else:
        return False


removeUserMutex = threading.Lock()


# 删除用户，关闭并销毁用户开启的docker，并且在排队中删除他（让他完全在系统缓存中消失）
def removeUser(username):
    removeUserMutex.acquire()
    try:
        if r.exists(_Str_User_to_Port + username):
            targetPort = r.get(_Str_User_to_Port + username)
            targetToken = r.get(_Str_User_to_Token + username)

            if r.exists(_Str_User_File_Save_Mode + username) and r.get(_Str_User_File_Save_Mode + username) == 0:
                pass
            else:
                targetPath = permanentTool.cleanPermanentPath(username)
                dockerTool.backupPermanentPath(targetPort, targetPath)

            # 删除docker操作
            dockerTool.removeContainer(targetPort)

            if r.exists(targetToken):
                r.delete(targetToken)

            r.delete(_Str_User_to_Port + username)
            r.delete(_Str_User_to_Token + username)

            r.delete(_Str_Port_to_User + targetPort)
            r.delete(_Str_Port_Start_Time + targetPort)

            r.delete(_Str_User_File_Save_Mode + username)
        if r.exists('vsUserList'):
            length = r.llen('vsUserList')
            if length > 0:
                r.lrem('vsUserList', 1, username)
    except Exception as re:
        print(re)
    removeUserMutex.release()
    return 1


def checkToken():
    _new_occupiedPort = []

    occupiedPortList = []
    for key in r.scan_iter("*"):
        if str(key).startswith(_Str_Port_to_User):
            tempPort = key.replace(_Str_Port_to_User, "", 1)
            occupiedPortList.append(tempPort)
    for targetPort in occupiedPortList:
        if r.exists(_Str_Port_Start_Time + str(targetPort)):
            username = r.get(_Str_Port_to_User + str(targetPort))
            targetToken = r.get(_Str_User_to_Token + username)
            starttime = int(r.get(_Str_Port_Start_Time + str(targetPort)))
            nowtime = int(time.time())
            # 最长使用时间限制
            # if nowtime - starttime > all_time:
            #     removeUser(username)
            # el
            if not r.exists(targetToken):
                removeUser(username)
            else:
                _new_occupiedPort.append(targetPort)
        else:
            print(str(targetPort), "不存在")
    return _new_occupiedPort


def extendLife(username):
    if r.exists(_Str_User_to_Port + username):
        targetPort = r.get(_Str_User_to_Port + username)
        r.set(_Str_Port_Start_Time + str(targetPort), int(time.time()))


# 获取用户对应的端口
# 获取失败返回None
def getPort(username):
    if r.exists(_Str_User_to_Token + username):
        targetToken = r.get(_Str_User_to_Token + username)
        if r.exists(targetToken):
            return r.get(targetToken)
        else:
            return None
    else:
        return None


# 获取用户对应的端口的Cookie
# 获取失败返回None
def getPortToken(username):
    if r.exists(_Str_User_to_Token + username):
        targetToken = r.get(_Str_User_to_Token + username)
        if r.exists(targetToken):
            return targetToken
        else:
            return None
    else:
        return None


def cleanRedis():
    for key in r.scan_iter("*"):
        r.delete(key)


def getUseTime(username):
    if r.exists(_Str_User_to_Token + username):
        targetToken = r.get(_Str_User_to_Token + username)
        if r.exists(targetToken):
            targetPort = r.get(targetToken)
            startTime = int(r.get(_Str_Port_Start_Time + str(targetPort)))
            useTime = int(time.time()) - startTime
            return startTime, useTime
        else:
            return 0, 0
    else:
        return 0, 0


def cleanUsedContainer():
    for key in r.scan_iter("*"):
        if str(key).startswith(_Str_User_to_Port):
            username = key.replace(_Str_User_to_Port, "", 1)
            removeUser(username)
    # for key in r.scan_iter("*"):
    #     if str(key).startswith(_Str_User_to_Port):
    #         targetPort = r.get(key)
    #         dockerTool.removeContainer(targetPort)


def collectUser():
    collecDict = {}
    for key in r.scan_iter("*"):
        if str(key).startswith(_Str_User_to_Port):
            targetPort = r.get(key)
            username = key.replace(_Str_User_to_Port, "", 1)
            collecDict[username] = targetPort
    return collecDict


def countUser():
    count = 0
    for key in r.scan_iter("*"):
        if str(key).startswith(_Str_User_to_Port):
            count += 1
    return count


def getPortList():
    occupiedPortList = []
    for key in r.scan_iter("*"):
        if str(key).startswith(_Str_Port_to_User):
            tempPort = key.replace(_Str_Port_to_User, "", 1)
            occupiedPortList.append(int(tempPort))
    return occupiedPortList


if __name__ == '__main__':
    r = redis.Redis(host='182.92.175.181', port=6379, decode_responses=True, password="kujiji555")
    collecDict = {}
    for key in r.scan_iter("*"):
        if str(key).startswith(_Str_User_to_Port):
            targetPort = r.get(key)
            username = key.replace(_Str_User_to_Port, "", 1)
            collecDict[username] = targetPort
    print(collecDict)
