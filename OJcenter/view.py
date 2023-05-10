# coding=utf-8
from __future__ import division

import logging
import os

import time

import json
import requests
import urllib

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from pytz import timezone
from OJcenter.Tool import systemTool, dockerTool, userTool, aesTool, k8sTool, redisTool
from .model import UserstatusDetail

cst_tz = timezone('Asia/Shanghai')
utc_tz = timezone('UTC')


def lockStatus(request):
    username = request.username
    if userTool.get_unlock_time(username):
        return HttpResponse(json.dumps({'result': 1}), content_type="application/json")
    return HttpResponse(json.dumps({'result': -1}), content_type="application/json")


def handleNotice(request):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    notification_ids = data['notification_ids']
    users = data['users']
    content = data['content']
    logging.info("notice body [content={}, users=[{}], notification_ids=[{}]]".format(
        content,
        ', '.join(users),
        ', '.join(notification_ids))
    )
    send_message(users, notification_ids, {"type": "notice", "body": {"id": -1, "message": content}})
    return HttpResponse("ok")


@async_to_sync
async def send_message(users, notification_ids, message):
    channel_layer = get_channel_layer()
    for i in range(len(users)):
        group_name = 'user_' + users[i]
        message['body']['id'] = notification_ids[i]
        await channel_layer.group_send(
            group_name,
            {
                'type': 'send_notice_message',
                'message': message
            },
        )

@csrf_exempt
def getUrl(request):
    try:
        username = request.username
        res = {"result": 1,"url": "/"}
        return HttpResponse(json.dumps(res), content_type="application/json")
    except Exception as re:
        faileddict = {"result": -1, "info": "异常错误"}
        return HttpResponse(json.dumps(faileddict), content_type="application/json")


@csrf_exempt
def getModel(request):
    try:
        username = request.username
        model = 1
        successdict = {"result": 1, "model": model}
        return HttpResponse(json.dumps(successdict), content_type="application/json")
    except Exception as e:
        print(e)
        faileddict = {"result": -1, "info": "异常错误"}
        return HttpResponse(json.dumps(faileddict), content_type="application/json")


def getCookie(request):
    username = systemTool.checkLogin(request)
    if username == None:
        faileddict = {"result": -100, "info": ""}
        return HttpResponse(json.dumps(faileddict), content_type="application/json")
    result = {"result": 1, "info": redisTool.getPortToken(username)}
    return HttpResponse(json.dumps(result), content_type="application/json")

@csrf_exempt
def getUsername(request):
    return HttpResponse(json.dumps({"result": 1, "info": request.username}), content_type="application/json")


@csrf_exempt
def insertUser(request):
    try:
        username = request.username
        status = redisTool.insertUser(username)
        successdict = {"result": 1, "info": status}
        return HttpResponse(json.dumps(successdict), content_type="application/json")
    except Exception as e:
        print(e)
        faileddict = {"result": -1, "info": "异常错误"}
        return HttpResponse(json.dumps(faileddict), content_type="application/json")


def orderResult(request):
    try:
        username = request.username
        targetToken = redisTool.queryUser(username)
        # templeMessage=messageTool.queryMessage(username)
        templeMessage = None
        if targetToken == False:
            targetOder = systemTool.getOrder(username)
            successdict = {"result": 1, "order": targetOder, "message": templeMessage}
            return successdict
        else:
            successdict = {"result": 1, "order": 0, "message": templeMessage}
            return successdict
    except Exception as e:
        print(e)
        faileddict = {"result": -1, "info": "异常错误"}
        return faileddict


def lockResult(request):
    try:
        username = request.username
        request.GET.get("cid")
        if username != None and UserstatusDetail.objects.filter(username=username, is_lock=1, is_unlock=0).count() > 0:
            targetPort = redisTool.getPort(username)
            command = "docker pause " + "ojDockerServer" + str(targetPort)
            os.system(command)
            return 1
        elif username != None and UserstatusDetail.objects.filter(username=username, is_lock=1,
                                                                  is_unlock=1).count() > 0:
            targetPort = redisTool.getPort(username)
            command = "docker unpause " + "ojDockerServer" + str(targetPort)
            os.system(command)
            return 0
    except Exception as e:
        print(e)
        return 0


@csrf_exempt
def getOrder(request):
    """
    try:
        username= systemTool.checkLogin(request)
        if username==None:
            faileddict = {"result": -100, "info": "未登录"}
            return HttpResponse(json.dumps(faileddict), content_type="application/json")

        targetToken = redisTool.queryUser(username)
        templeMessage=messageTool.queryMessage(username)
        if targetToken == False:
            targetOder = systemTool.getOrder(username)
            successdict = {"result": 1, "order": targetOder,"message":templeMessage}
            return HttpResponse(json.dumps(successdict), content_type="application/json")
        else:
            successdict = {"result": 1, "order": 0,"message":templeMessage}
            return HttpResponse(json.dumps(successdict), content_type="application/json")
    except Exception as e:
        print(e)
        faileddict = {"result": -1, "info": "异常错误"}
        return HttpResponse(json.dumps(faileddict), content_type="application/json")
    """
    return HttpResponse(json.dumps(orderResult(request)), content_type="application/json")


@csrf_exempt
def checkAlive(request):
    ret = orderResult(request)
    ret["lock"] = lockResult(request)
    return HttpResponse(json.dumps(ret), content_type="application/json")


@csrf_exempt
def removeUser(request):
    try:
        username = request.username
        redisTool.removeUser(username)

        successdict = {"result": 1}
        ret = HttpResponse(json.dumps(successdict), content_type="application/json")
        ret.delete_cookie("cdrID")
        return ret
    except Exception as e:
        print(e)
        faileddict = {"result": -1, "info": "异常错误"}
        return HttpResponse(json.dumps(faileddict), content_type="application/json")


def init():
    # 更新docker版本时使用
    # dockerTool.cleanContainers()

    # 需要清理所有用户时使用
    # 更新版本的时候取消注释
    # redisTool.cleanUsedContainer()
    # redisTool.cleanRedis()

    # 清点所有容器，并且随时创建新容器
    # systemTool.refreshCreatedPort()
    try:
        systemTool.initK8sPod()
    except:
        pass
    # 把队首的人拿出来
    systemTool.refreshOrder()
    # dockerTool.refreshthread()
    return None


# def login(request):
#     try:
#         print(request.method)
#         postBody = request.body
#         json_result = json.loads(postBody)
#         username = json_result['username']
#         password = json_result['password']
#         if systemTool.login(username, password):
#             targetToken=redisTool.loginToken(username)
#             successdict = {"result": 1, "tokens": targetToken}
#             return HttpResponse(json.dumps(successdict), content_type="application/json")
#         else:
#             faileddict = {"result": 0, "info": "账号或密码有误"}
#             return HttpResponse(json.dumps(faileddict), content_type="application/json")
#     except Exception as e:
#         faileddict = {"result": -1, "info": "异常错误"}
#         return HttpResponse(json.dumps(faileddict), content_type="application/json")


@csrf_exempt
def getUserPort(request):
    try:
        username = request.username
        port = redisTool.getPort(username)

        successdict = {"result": 1, "port": port}
        return HttpResponse(json.dumps(successdict), content_type="application/json")
    except Exception as e:
        print(e)
        faileddict = {"result": -1, "info": "异常错误"}
        return HttpResponse(json.dumps(faileddict), content_type="application/json")


def getUserToken(request):
    try:
        username = request.username
        portToken = redisTool.getPortToken(username)

        successdict = {"result": 1, "token": portToken}
        return HttpResponse(json.dumps(successdict), content_type="application/json")
    except Exception as e:
        print(e)
        faileddict = {"result": -1, "info": "异常错误"}
        return HttpResponse(json.dumps(faileddict), content_type="application/json")


def getUseTime(request):
    try:
        username = request.username
        startTime, useTime = redisTool.getUseTime(username)

        successdict = {"result": 1, "starttime": startTime, "usetime": useTime}
        return HttpResponse(json.dumps(successdict), content_type="application/json")
    except Exception as e:
        print(e)
        faileddict = {"result": -1, "info": "异常错误"}
        return HttpResponse(json.dumps(faileddict), content_type="application/json")

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    elif request.META.get('HTTP_X_REAL_IP'):
        ip = request.META.get('HTTP_X_REAL_IP')
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def getSubmitAnswer(request):
    try:
        # 修改username获取方式
        """
        print(request.method)
        postBody = request.body
        json_result = json.loads(postBody)
        username = json_result['username']
        """
        language = request.POST["language"]
        id = int(request.POST["id"])
        cid = int(request.POST["cid"])
        pid = int(request.POST["pid"])
        # ip=get_client_ip(request)
        ip = str(request.POST["ip"])
        password = str(request.POST["password"])
        username = str(request.POST["username"])

        languageint = 0
        if language == "cpp":
            languageint = 1
        elif language == "c":
            languageint = 0
        elif language == "py":
            languageint = 6
        elif language == "java":
            languageint = 3

        targetPort = redisTool.getPort(username)
        # souce = dockerTool.getContainerFile(targetPort, language)
        source = k8sTool.getTargetFile(targetPort, language)

        url = 'http://127.0.0.1:2336/vsbuctojsubmit.php'
        if cid == 0:
            d = {"user_id": username,
                 "password": "ASisends926002hspsJis9eIesk",
                 "language": languageint,
                 "source": source,
                 "VSmode": 1,
                 "ip": ip,
                 "id": id}
        else:
            d = {"user_id": username,
                 "password": "ASisends926002hspsJis9eIesk",
                 "language": languageint,
                 "source": source,
                 "VSmode": "1",
                 "cid": cid,
                 "ip": ip,
                 "pid": pid}
        r = requests.post(url, data=d)
        print(d)
        successdict = {"code": 1, "msg": "成功"}
        return HttpResponse(json.dumps(successdict), content_type="application/json")
    except Exception as e:
        print(e)
        faileddict = {"code": -1, "msg": "异常错误"}
        return HttpResponse(json.dumps(faileddict), content_type="application/json")


def getEditCode(request):
    try:
        username = request.username
        id = request.POST["p3"]

        url = 'http://127.0.0.1:2336/showsource3.php?id=' + id + '&username=' + username + '&password=ASiend92600spJi9eIesk'
        r = requests.get(url)
        s = r.json()
        code = s["code"]
        lang = int(s["language"])
        language = "cpp"
        if lang == 0:
            language = "c"
        elif lang == 1:
            language = "cpp"
        elif lang == 6:
            language = "py"

        targetPort = redisTool.getPort(username)
        code = str(code)
        currentTime = time.strftime("%H:%M:%S", time.localtime())
        dockerTool.writeContainerFile(targetPort, code, id + "-" + currentTime, language)

        url = 'http://127.0.0.1:2336/reinfo2.php?id=' + id + '&username=' + username + '&password=ASiend92600spJi9eIesk'
        r = requests.get(url)
        try:
            s = r.json()
            str_in = str(s["str_in"])
            str_out = str(s["str_out"])
            if str_in is not None and len(str_in) > 0:
                dockerTool.writeContainerFile(targetPort, str_in, id + "-" + currentTime + "-input", "txt")
            if str_out is not None and len(str_out) > 0:
                dockerTool.writeContainerFile(targetPort, str_out, id + "-" + currentTime + "-output", "txt")
        except Exception as e:
            print(e)

        successdict = {"code": 1, "msg": "成功"}
        return HttpResponse(json.dumps(successdict), content_type="application/json")
    except Exception as e:
        print(e)
        faileddict = {"code": -1, "msg": "获取信息失败，请检查你的登录状态，或当前是否处于考试模式"}
        return HttpResponse(json.dumps(faileddict), content_type="application/json")


def getMessage(request):
    try:
        username = request.username
        startTime, useTime = redisTool.getUseTime(username)

        successdict = {"result": 1, "starttime": startTime, "usetime": useTime}
        return HttpResponse(json.dumps(successdict), content_type="application/json")
    except Exception as e:
        print(e)
        faileddict = {"result": -1, "info": "异常错误"}
        return HttpResponse(json.dumps(faileddict), content_type="application/json")


def checkStatus(request):
    try:
        username = request.username
        status = request.POST["status"]
        detail = request.POST["detail"]
        userTool.testBan(username, status, detail)

        successdict = {"result": 1}
        return HttpResponse(json.dumps(successdict), content_type="application/json")
    except Exception as e:
        print(e)
        faileddict = {"result": -1, "info": "异常错误"}
        return HttpResponse(json.dumps(faileddict), content_type="application/json")


def getEditCodeUpdate(request):
    try:
        if request.META.get('HTTP_X_FORWARDED_FOR'):
            ip = request.META.get("HTTP_X_FORWARDED_FOR")
        else:
            ip = request.META.get("REMOTE_ADDR")
        # username= systemTool.checkLogin(request)
        # if username==None:
        #     faileddict = {"result": -100, "info": "未登录"}
        #     return HttpResponse(json.dumps(faileddict), content_type="application/json")

        # filename = request.POST["filename"]
        # content = request.POST["content"]
        # language = request.POST["language"]
        # key = request.POST["key"]
        # keycode = request.POST["keycode"]
        # problemid: problemid, contestid: contestid
        # problemid = request.POST["problemid"]
        # contestid = request.POST["contestid"]
        # userTool.updateUserCodeExtension(username,filename,content,language)

        content = request.POST["content"]
        contentJson = json.loads(content)
        filename = contentJson["filename"]
        contentStr = contentJson["content"]
        finalcontentStr = urllib.parse.unquote(contentStr)
        language = contentJson["language"]
        auth = contentJson["auth"]
        decodeob = aesTool.AESCipher("1p0d[a;'.tjg94'h[5[h.f.s''43'wds;f[a]g'f[[,25474-=f-sa-")
        username = decodeob.decrypt(auth)

        userTool.updateUserCodeExtension(username, filename, finalcontentStr, language)

        successdict = {"result": 1}
        return HttpResponse(json.dumps(successdict), content_type="application/json")
    except Exception as e:
        print(e)
        faileddict = {"result": -1, "info": "异常错误"}
        return HttpResponse(json.dumps(faileddict), content_type="application/json")


# def getEditCodeUpdate(request):
#     try:
#         username= systemTool.checkLogin(request)
#         if username==None:
#             faileddict = {"result": -100, "info": "未登录"}
#             return HttpResponse(json.dumps(faileddict), content_type="application/json")
#
#         filename = request.POST["filename"]
#         content = request.POST["content"]
#         language = request.POST["language"]
#         key = request.POST["key"]
#         keycode = request.POST["keycode"]
#         #problemid: problemid, contestid: contestid
#         problemid = request.POST["problemid"]
#         contestid = request.POST["contestid"]
#         userTool.updateUserCode(username,filename,content,language,key,keycode,contestid,problemid)
#
#         successdict = {"result": 1}
#         return HttpResponse(json.dumps(successdict), content_type="application/json")
#     except Exception as e:
#         print(e)
#         faileddict = {"result": -1, "info": "异常错误"}
#         return HttpResponse(json.dumps(faileddict), content_type="application/json")


def entercontest(request):
    try:
        username = request.username
        contestid = request.POST["contest"]
        status = systemTool.entercontest(username, contestid)
        if status == 1:
            successdict = {"result": 1, "info": 1}
            return HttpResponse(json.dumps(successdict), content_type="application/json")
        elif status == 0:
            successdict = {"result": 1, "info": 0}
            return HttpResponse(json.dumps(successdict), content_type="application/json")
    except Exception as e:
        print(e)
        faileddict = {"result": -1, "info": "异常错误"}
        return HttpResponse(json.dumps(faileddict), content_type="application/json")


def onlinecount(request):
    try:
        username = request.username
        count = redisTool.countUser()
        successdict = {"result": 1, "info": count}
        return HttpResponse(json.dumps(successdict), content_type="application/json")
    except Exception as e:
        print(e)
        faileddict = {"result": -1, "info": "异常错误"}
        return HttpResponse(json.dumps(faileddict), content_type="application/json")


def getAccessCodeServer(request):
    try:
        username = request.username
        cookie = redisTool.getPortToken(username)
        successdict = {"result": 1, "info": cookie}
        return HttpResponse(json.dumps(successdict), content_type="application/json")
    except Exception as e:
        print("Exception in getAccessCodeServer: \n%s" % e)
        faileddict = {"result": -1, "info": "异常错误"}
        return HttpResponse(json.dumps(faileddict), content_type="application/json")

def getAccessCodeServerSimple(request):
    try:
        username = request.POST['username']
        password = request.POST['password']
        if password !="as055dSg54W6eA5423412":
            faileddict = {"result": -100, "info": "未登录"}
            return HttpResponse(json.dumps(faileddict), content_type="application/json")
        cookie = redisTool.getPortToken(username)
        successdict = {"result": 1, "info": cookie}
        return HttpResponse(json.dumps(successdict), content_type="application/json")
    except Exception as e:
        print(e)
        faileddict = {"result": -1, "info": "异常错误"}
        return HttpResponse(json.dumps(faileddict), content_type="application/json")
