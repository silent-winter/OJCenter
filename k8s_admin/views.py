import datetime
import json
import _thread
import time
import redis
import re

from django.http import HttpResponse
from django.utils import timezone

from OJcenter import context
from OJcenter.Tool import k8sTool, redisTool, messageTool
from OJcenter.model import PodRecord, UserUseLog

pool = redis.ConnectionPool(host=context.getHost(), port=6379, decode_responses=True)
r = redis.Redis(connection_pool=pool)


def list_user(request):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    page, size, prop, order = data['page'], data['size'], data['prop'], data['order']
    pod_metrics_list = k8sTool.get_pod_metrics()['items']
    metrics_map = {pod['metadata']['name']: pod['containers'][0]['usage'] for pod in pod_metrics_list}

    res = []
    user_keys = r.keys('UserPort:*')
    for user_key in user_keys:
        username = user_key.split(':')[1]
        port = r.get(user_key)
        start_time = r.get('PortStartTime:' + port)
        start_time = datetime.datetime.fromtimestamp(int(start_time)).strftime('%Y-%m-%d %H:%M:%S')
        user_token = r.get("UserToken:" + username)
        pod = k8sTool.getPod(port)
        pod_name = pod.metadata.name
        pod_status = pod.status.phase
        node_name = pod.spec.node_name
        memory = str(round(int(metrics_map[pod_name]['memory'][:-2]) / 1024.0, 2)) + 'MB' if pod_name in metrics_map else '暂无数据'
        cpu = str(round(int(metrics_map[pod_name]['cpu'][:-1]) / 1000000, 2)) + 'm' if pod_name in metrics_map else '暂无数据'
        res.append({"username": username, "podName": pod_name, "podStatus": pod_status, "nodeName": node_name,
                    "startUseTime": start_time, "userToken": user_token, "cpu": cpu, "memory": memory})
    # 排序
    if prop != '' and order != '':
        if prop == 'memory':
            res = sorted(res, key=lambda x: float(x.get(prop)[:-2]), reverse=False if order == 'ascending' else True)
        elif prop == 'cpu':
            res = sorted(res, key=lambda x: float(x.get(prop)[:-1]), reverse=False if order == 'ascending' else True)
        else:
            res = sorted(res, key=lambda x: x.get(prop), reverse=False if order == 'ascending' else True)
    length = len(res)
    if length > size:
        start_index = (page - 1) * size
        end_index = min(start_index + size, length)
        res = res[start_index:end_index]
    response = {'total': length, "data": res}
    return HttpResponse(json.dumps(response), content_type="application/json")


def list_node(request):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    page, size = data['page'], data['size']
    node_metrics = k8sTool.get_node_metrics()['items']
    res = []
    for node in node_metrics:
        memory = str(round(int(node["usage"]["memory"][:-2]) / 1024.0, 2)) + 'MB'
        cpu = str(round(int(node["usage"]["cpu"][:-1]) / 1000000, 2)) + 'm'
        res.append({"name": node["metadata"]["name"], "labels": node["metadata"]["labels"], "memory": memory, "cpu": cpu})
    response = {"total": len(res), "data": res}
    return HttpResponse(json.dumps(response), content_type="application/json")


def migrate(request, pod_name):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    username = data['username']
    k8sTool.deletePod(pod_name)
    messageTool.websocket_send_message(username, {"type": "migrate", "body": {}})
    return HttpResponse("success")


def kick(request, username):
    redisTool.removeUser(username)
    messageTool.websocket_send_message(username, {"type": "kick", "body": {"reason": "系统检测到异常行为，你已被停止使用"}})
    return HttpResponse("success")


def list_for_resource(request, name):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    start_time, end_time = data['start_time'], data['end_time']
    one_hour_ago = (datetime.datetime.now() - datetime.timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
    if re.match(r"server-(\d+)-(\w+)-(\w+)", name) is not None:
        if start_time != '' and end_time != '':
            tmp = PodRecord.objects.filter(pod_name=name, update_time__gte=data['start_time'],
                                           update_time__lte=data['end_time']).order_by('update_time')
        else:
            tmp = PodRecord.objects.filter(pod_name=name, update_time__gt=one_hour_ago).order_by('update_time')
    else:
        if start_time != '' and end_time != '':
            tmp = PodRecord.objects.filter(username=name, update_time__gte=data['start_time'],
                                           update_time__lte=data['end_time']).order_by('update_time')
        else:
            tmp = PodRecord.objects.filter(username=name, update_time__gt=one_hour_ago).order_by('update_time')
    res = []
    for item in tmp:
        # print(item.username, item.cpu, item.memory, item.updatetime, item.podname)
        res.append({"username": item.username, "podName": item.pod_name,
                    "updateTime": item.update_time.strftime('%Y-%m-%d %H:%M:%S'), "cpu": item.cpu, "memory": item.memory})
                    
    response = {"total": len(res), "data": res}
    return HttpResponse(json.dumps(response), content_type="application/json")


def list_for_user_history(request):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    page, size, text = data['page'], data['size'], data['text']
    if text != '':
        user_use_log_list = UserUseLog.objects.filter(username__icontains=text).order_by("-start_time").all()
    else:
        user_use_log_list = UserUseLog.objects.order_by("-start_time").all()
    res = list(user_use_log_list.values())
    for item in res:
        item['start_time'] = item['start_time'].strftime('%Y-%m-%d %H:%M:%S')
    length = len(res)
    if length > size:
        start_index = (page - 1) * size
        end_index = min(start_index + size, length)
        res = res[start_index:end_index]
    response = {'total': length, "data": res}
    return HttpResponse(json.dumps(response), content_type="application/json")


def recordPodStatus():
    r = redis.Redis(host=context.getHost(), port=6379, decode_responses=True)

    while True:

        pod_metrics_list = k8sTool.get_pod_metrics()['items']
        metrics_map = {pod['metadata']['name']: pod['containers'][0]['usage'] for pod in pod_metrics_list}
        user_keys = r.keys('UserPort:*')

        for user_key in user_keys:
            username = user_key.split(':')[1]
            curr_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            port = r.get(user_key)

            pod = k8sTool.getPod(port)
            pod_name = pod.metadata.name
            memory = round(int(metrics_map[pod_name]['memory'][:-2]) / 1024.0, 2) if pod_name in metrics_map else 0
            cpu = round(int(metrics_map[pod_name]['cpu'][:-1]) / 1000000, 2) if pod_name in metrics_map else 0

            user_status_detail = PodRecord(username=username, cpu=cpu, memory=memory, pod_name=pod_name)
            user_status_detail.save()

        time.sleep(10)

def init():
    try:
        _thread.start_new_thread(recordPodStatus, ())
    except Exception as e:
        print("资源记录线程出错")
        print(e)