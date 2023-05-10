import configparser
import logging
import sys
import datetime

import MySQLdb
import pandas
import pandas as pd
from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.utils import timezone

from OJcenter.Tool import redisTool
from OJcenter.model import UserstatusDetail


@sync_to_async
def is_lock(username):
    return UserstatusDetail.objects.filter(username=username, is_lock=1, is_unlock=0).count() > 0


@sync_to_async
def get_unlock_time(username):
    cache_key = f"get_unlock_time:{username}"
    value = cache.get(cache_key)
    if value is not None:
        return value
    user_status_detail = UserstatusDetail.objects.filter(username=username, is_lock=1, is_unlock=0).order_by('-id').first()
    if user_status_detail:
        auto_unlock_time = user_status_detail.autounlock_time
        if auto_unlock_time:
            cache.set(cache_key, auto_unlock_time)
            return auto_unlock_time
    return None


def codeCheck(detail):
    tokens = ["include", "for(", "int", "double", "namespace", "float", "memset", "stdio.h",
              "iostream", "scanf", "printf", "cin", "cout", "struct", "scanf", "void", "if", "break",
              "return", "continue"]
    for token in tokens:
        if token in detail:
            return 1


def ban(username, status, detail):
    try:
        curr_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        # db = MySQLdb.connect("localhost", "debian-sys-maint", "DOZtOQzgvY1oFXb1", "record", charset='utf8')
        # cursor = db.cursor()
        # query = """insert into userstatus_detail (username, contest_id, problem_id,
        # status, pastetime, paste_label, detail, is_lock, is_unlock, updatetime) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        # values = (
        #     username, "no", "no", status, time_str, "0", detail, "1", "0", time_str)
        # cursor.execute(query, values)
        # db.commit()
        # db.close()
        user_status_detail = UserstatusDetail(username=username, contest_id="no", problem_id="no", status=status,
                                              pastetime=curr_time, paste_label="0", detail=detail, is_lock="1",
                                              is_unlock="0", updatetime=curr_time, autounlock_time="2023-06-10 23:00:00")
        user_status_detail.save()
        # port = redisTool.getPort(username)
        # command = "docker pause " + "ojDockerServer" + str(targetPort)
        # os.system(command)
        # 这里需要修改为: websocket通知前端, 展示封号弹窗, 并退回首页
        send_message(username)
        redisTool.removeUser(username)
    except Exception as re:
        logging.error("Exception in ban user: %s", re)


@async_to_sync
async def send_message(username):
    channel_layer = get_channel_layer()
    group_name = 'user_' + username
    await channel_layer.group_send(group_name, {
        'type': 'send_notice_message',
        'message': {'type': 'check-status', 'body': {'result': 'ban'}}
    })


def testBan(username, status, detail):
    ban(username, status, detail)


def updateUserStatus(username, status, detail):
    try:
        curr_time = datetime.datetime.now()
        time_str = datetime.datetime.strftime(curr_time, '%Y-%m-%d %H:%M:%S')
        db = MySQLdb.connect("localhost", "debian-sys-maint", "DOZtOQzgvY1oFXb1", "record", charset='utf8')
        cursor = db.cursor()
        query = """insert into userstatus (username, status, detail,updatetime) values (%s,%s,%s,%s)"""
        values = (
            username, status, detail, time_str)
        cursor.execute(query, values)
        db.commit()
        if "paste" in status:
            cf = getConfiguration()
            maxNum = int(cf.get("portconfig", "maxNum"))
            query = "select detail from userstatus where (status like %s or status like %s)  and username = %s ORDER " \
                    "BY id DESC limit %s "
            values = ("cut%", "copy%", username, maxNum)
            cursor.execute(query, values)
            db.commit()
            result = cursor.fetchall()
            # afterDetail和ans是为了去除换行符，即windows和linux下的换行符的差异
            afterDetail = detail.replace('\n', '')
            afterDetail = afterDetail.replace('\r', '')
            if len(result) == 0:
                if codeCheck(detail) == 1:
                    ban(username, status, detail)
            else:
                flag = 1
                df = pandas.DataFrame(list(result))

                for i in range(len(df)):
                    ans = df.iat[i, 0].replace('\n', '')
                    ans = ans.replace('\r', '')
                    if ans == afterDetail:
                        flag = 0
                        break
                if flag == 1:
                    if codeCheck(detail) == 1:
                        ban(username, status, detail)
        db.close()
    except Exception as re:
        print(re)


def getConfiguration():
    path = sys.path[0] + "/OJcenter/Tool/config.ini"
    cf = configparser.ConfigParser()
    cf.read(path)
    return cf


def updateUserCode(username, fileName, content, language, key, keycode, contestid, problemid):
    try:
        curr_time = datetime.datetime.now()
        time_str = datetime.datetime.strftime(curr_time, '%Y-%m-%d %H:%M:%S')

        userDict = redisTool.collectUser()
        targetPort = userDict[username]
        db = MySQLdb.connect("localhost", "debian-sys-maint", "DOZtOQzgvY1oFXb1", "record", charset='utf8')
        cursor = db.cursor()
        query = """insert into collectinfo (username, targetport, fileaddress,modifytime, codetype, modifycode, 
        updatetime, contestid, problemid, action,keynumber,keycode) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) """
        values = (
            username, targetPort, fileName, time_str, language, content, time_str, contestid, problemid, "", key,
            keycode)
        cursor.execute(query, values)
        db.commit()
    except Exception as re:
        print(re)


def updateUserCodeExtension(username, fileName, content, language):
    try:
        curr_time = datetime.datetime.now()
        time_str = datetime.datetime.strftime(curr_time, '%Y-%m-%d %H:%M:%S')
        username = username.split(" ")[0]

        userDict = redisTool.collectUser()
        targetPort = userDict[username]
        db1 = MySQLdb.connect("localhost", "debian-sys-maint", "DOZtOQzgvY1oFXb1", "jol", charset='utf8')
        # 查找时间对应的题目和竞赛
        cursor2 = db1.cursor()
        cursor2.execute(
            'select username, problem, time from pagevisit where username=%s and time <%s order by time desc limit 1',
            (username, time_str))
        data = cursor2.fetchall()
        data = pd.DataFrame(list(data), columns=['username', 'problem', 'time'])
        visittime = data['time']
        if len(visittime) > 0:
            problem = data['problem'][0]
            if '+' in problem:
                contestid = problem.split('+', 2)[0]
                if problem[-1] == "+":
                    problemid = ""
                else:
                    problemid = problem.split('+', 2)[1]
            else:
                problemid = problem
                contestid = ""

        db = MySQLdb.connect("localhost", "debian-sys-maint", "DOZtOQzgvY1oFXb1", "record", charset='utf8')
        cursor = db.cursor()
        query = """insert into collectinfo (username, targetport, fileaddress,modifytime, codetype, modifycode, 
        updatetime, contestid, problemid, action,keynumber,keycode) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) """
        values = (
            username, targetPort, fileName, time_str, language, content, time_str, contestid, problemid, "", "", "")
        cursor.execute(query, values)
        db.commit()
    except Exception as re:
        print(re)
