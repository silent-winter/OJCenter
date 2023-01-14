# coding=utf-8
from __future__ import division

import time

import json
import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from pytz import timezone
from OJcenter.Tool import systemTool, redisTool, dockerTool, userTool, messageTool

cst_tz = timezone('Asia/Shanghai')
utc_tz = timezone('UTC')


def userlist(request):
    try:
        username = systemTool.checkLogin(request)
    except Exception as e:
        print(e)
        faileddict = {"code": -1, "msg": "异常错误"}
        return HttpResponse(json.dumps(faileddict), content_type="application/json")


def usermonitor(request):
    return None
