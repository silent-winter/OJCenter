import datetime
import json

import redis
from django.http import HttpResponse

# Create your views here.
from OJcenter import context
from OJcenter.Tool import k8sTool, redisTool

pool = redis.ConnectionPool(host=context.getHost(), port=6379, decode_responses=True)
r = redis.Redis(connection_pool=pool)


def list_for_data(request):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    page, size = data['page'], data['size']
    pod_metrics_list = k8sTool.get_metrics()['items']
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
    length = len(res)
    if length > size:
        start_index = (page - 1) * size
        end_index = min(start_index + size, length)
        res = res[start_index:end_index]
    response = {'total': length, "data": res}
    return HttpResponse(json.dumps(response), content_type="application/json")


def migrate(request, pod_name):
    k8sTool.deletePod(pod_name)
    return HttpResponse("success")


def kick(request, username):
    redisTool.removeUser(username)
    return HttpResponse("success")
