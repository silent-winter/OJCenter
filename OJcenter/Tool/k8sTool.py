import os
import shutil
import time
from typing import Optional
import urllib3

from retry import retry

from kubernetes import client
from kubernetes.client import V1Pod, V1PodList, V1PersistentVolumeClaim, V1Service
from kubernetes.client.rest import ApiException

from OJcenter import context
from OJcenter.Tool import aesTool, timeTool, redisTool
from OJcenter.model import PodMetaInfo

# 获取apiserver token
# kubectl -n kubernetes-dashboard get secret $(kubectl -n kubernetes-dashboard get sa/admin-user -o jsonpath="{.secrets[0].name}") -o go-template="{{.data.token | base64decode}}"
# api文档
# https://github.com/kubernetes-client/python/blob/master/kubernetes/docs
token = 'eyJhbGciOiJSUzI1NiIsImtpZCI6InplR3dYNXRsbW80bmRJaU82bS1OSE8weXdJRDlHMDN0d2RzUDJ5WGg1SDgifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlcm5ldGVzLWRhc2hib2FyZCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhZG1pbi11c2VyLXRva2VuLWs3OTZzIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImFkbWluLXVzZXIiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiIzOTdjNzY5NS0xZDdhLTRmZmQtOTZlMi00NTkxNTNkOWI4OTIiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZXJuZXRlcy1kYXNoYm9hcmQ6YWRtaW4tdXNlciJ9.cNx9hshVWHoZHjK5ZF0HCCf7xh4sb4YIW4thbIC6Z8HfFi-W4DkTQoh5AnFbv9_DY8zllydsg8AcOobZvNLiGh2F-LFizETdmZ8NUh6o2QQhrXxsidcorl9zSZb-8CbqBgzTGqj1_KNXRptdORxk_PAVuQVDyKPdePnYkkMGgYxlNlXcOsZZEUXjDC5zHdpTZupR7ZXYCN92RKqwDIjE1hMzBwEsdK0xFFZ0P9t_UOec95Bp_n3wSO2XLhuJdrxCQX69o2NikCZz-XjiZJbSAMjJMC-EeIVSaxjHs2orkBhzSdh8nf1dmCRl2JP3wYIZiy4VdgeDXZyOnHITbMH1BA'
apiServer = 'https://202.4.155.97:6443'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

configuration = client.Configuration()
setattr(configuration, 'verify_ssl', False)
client.Configuration.set_default(configuration)
configuration.host = apiServer
configuration.verify_ssl = False
configuration.debug = True
configuration.api_key = {"authorization": "Bearer " + token}
client.Configuration.set_default(configuration)

coreApi = client.CoreV1Api(client.ApiClient(configuration))
appsApi = client.AppsV1Api(client.ApiClient(configuration))

# 记录最后一个pod的主机端口
_port = 0
_maxPort = 32610
_end = -1


def init(start, end):
    global _port, _end
    _port = end + 1
    _end = end
    result = []
    for i in range(start, end + 1):
        pod = create(i)
        if pod is not None:
            result.append(pod)
            time.sleep(2)
    return result


# 创建n个pod
def batchCreate(n):
    global _port
    result = []
    while n > 0:
        pod = create(_port)
        if pod is not None:
            result.append(pod)
            n = n - 1
        _port = _port + 1
        if _port == _maxPort:
            _port = _end + 1
    return result


def create(port) -> Optional[PodMetaInfo]:
    if redisTool.existPod(port):
        return None
    pvcName = "pvc-%s" % port
    svcName = "svc-%s" % port
    createPvc(pvcName)
    createPod(port)
    pvName = getPvName(pvcName)
    # 初始化文件
    pvPath = "/nfs/data/default-%s-%s" % (pvcName, pvName)
    # os.system("cp -rp /nfs/data/base/test/  %s/" % pvPath)
    # os.system("cp -rp /nfs/data/base/answer/  %s/" % pvPath)
    # os.system("cp -rp /nfs/data/base/.vscode/  %s/" % pvPath)
    print("create pod success, port=%s, pvPath=%s" % (port, pvPath))
    return PodMetaInfo(port, pvPath, getClusterIp(svcName))


def createPod(port) -> V1Pod:
    # http://www.wetools.com/yaml/ yaml转json
    # https://www.json.cn/json/jsonzip.html 压缩json
    nodes = context.getAllKeys("node-config")
    # 设置节点亲和性
    affinity = ','.join(
        [
            '{{"preference":{{"matchExpressions":[{{"key":"{}/vscode-limit","operator":"Gt","values":["{}"]}}]}},"weight":{}}}'.format(
                node, podCountByNodeName(node), context.getConfigValue("node-config", node)
            )
            for node in nodes
        ]
    )
    bodyStr = '{{"apiVersion":"v1","kind":"Pod","metadata":{{"namespace":"default","name":"server-%s","labels":{{"app":"oj-k8s-server","id":"%s"}}}},"spec":{{"affinity":{{"nodeAffinity":{{"preferredDuringSchedulingIgnoredDuringExecution":[{}]}}}},"initContainers":[{{"name":"init-server","image":"server_20230323:latest","imagePullPolicy":"IfNotPresent","command":["/bin/sh","-c","cp -R /config/workspace/. /mnt"],"volumeMounts":[{{"name":"shared-workspace","mountPath":"/mnt"}}]}}],"containers":[{{"name":"server","image":"server_20230323:latest","imagePullPolicy":"IfNotPresent","lifecycle":{{"postStart":{{"exec":{{"command":["/bin/sh","-c","cp -R /mnt/. /config/workspace"]}}}}}},"ports":[{{"name":"vscode","containerPort":8443}}],"volumeMounts":[{{"name":"shared-workspace","mountPath":"/mnt"}},{{"name":"workspace-volume","mountPath":"/config/workspace"}}],"resources":{{"limits":{{"memory":"512Mi"}},"requests":{{"memory":"300Mi"}}}}}}],"volumes":[{{"name":"shared-workspace","emptyDir":{{}}}},{{"name":"workspace-volume","persistentVolumeClaim":{{"claimName":"pvc-%s"}}}}]}}}}'.format(
        affinity) % (port, port, port)
    body = eval(bodyStr)
    pod = coreApi.create_namespaced_pod(body=body, namespace="default", async_req=False)
    return pod


def deletePod(name) -> V1Pod:
    try:
        return coreApi.delete_namespaced_pod(name, "default")
    except ApiException as e:
        print("Exception when calling CoreV1Api->delete_namespaced_pod: %s\n" % e)


def createPvc(pvcName) -> Optional[V1PersistentVolumeClaim]:
    """
    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
      name: pvc-1
    spec:
      resources:
        requests:
          storage: 10M
      accessModes:
        - ReadWriteMany
      storageClassName: managed-nfs-storage
    """
    if isPvcExist(pvcName):
        print("pvcName=" + pvcName + " is exist")
        return None
    body = eval(
        '{"apiVersion":"v1","kind":"PersistentVolumeClaim","metadata":{"name":"' + pvcName + '"},"spec":{"resources":{"requests":{"storage":"10M"}},"accessModes":["ReadWriteMany"],"storageClassName":"managed-nfs-storage"}}')
    pvc = coreApi.create_namespaced_persistent_volume_claim(namespace="default", body=body)
    return pvc


def deletePvc(pvcName):
    try:
        return coreApi.delete_namespaced_persistent_volume_claim(pvcName, "default")
    except ApiException as e:
        print("Exception when calling CoreV1Api->delete_namespaced_persistent_volume_claim: %s\n" % e)


@retry(tries=5, delay=1)
def getPvName(pvcName):
    try:
        pvc = coreApi.read_namespaced_persistent_volume_claim(name=pvcName, namespace="default")
        pvName = pvc.to_dict()["spec"]["volume_name"]
        assert pvName is not None
        return pvName
    except ApiException as e:
        print("Exception when calling CoreV1Api->read_namespaced_persistent_volume_claim: %s\n" % e)
        return ""


@retry(tries=5, delay=1)
def getHostIp(podName):
    try:
        pod = coreApi.read_namespaced_pod(name=podName, namespace="default")
        hostIp = pod.to_dict()["status"]["host_ip"]
        assert hostIp is not None
        return hostIp
    except ApiException as e:
        print("Exception when calling CoreV1Api->read_namespaced_pod: %s\n" % e)
        return ""


def getClusterIp(svcName):
    svc = coreApi.read_namespaced_service(name=svcName, namespace="default")
    return svc.spec.cluster_ip


def listPodForAllNamespaces() -> V1PodList:
    podList = coreApi.list_pod_for_all_namespaces(watch=False)
    print("Listing pods with their IPs:")
    for item in podList.items:
        print("%s\t%s\t%s" % (item.status.pod_ip, item.metadata.namespace, item.metadata.name))
    return podList


def isPodExist(podName):
    podList = coreApi.list_namespaced_pod(field_selector=f'metadata.name={podName}', namespace="default")
    return len(podList.items) == 1


def isPvcExist(pvcName):
    pvcList = coreApi.list_namespaced_persistent_volume_claim(field_selector=f'metadata.name={pvcName}', namespace="default")
    return len(pvcList.items) == 1


def podCountByNodeName(nodeName):
    podList = coreApi.list_namespaced_pod(field_selector=f'spec.nodeName={nodeName}', namespace="default",
                                          label_selector='app=oj-k8s-server')
    return len(podList.items)


def copyPermanentFolder(username, pvPath):
    userPath = "/dockerdir/userfolder/%s/answer" % username
    answerPath = pvPath + "/answer"
    if os.path.exists(answerPath):
        shutil.rmtree(answerPath)
    shutil.copytree(userPath, answerPath)
    # 设置文件所有者
    os.system("chown -R nobody:nogroup %s/answer" % pvPath)
    currTime = timeTool.getCurrTime()
    authFile = "/dockerdir/userfolder/%s/authorization" % username
    if os.path.exists(authFile):
        os.remove(authFile)
    code = aesTool.getEncrypt(username + ' ' + currTime)
    with open(file=authFile, mode="w") as f:
        f.write(code.decode())
    shutil.copyfile(authFile, pvPath + "/.vscode/authorization")


def backupAnswer(userPath, pvPath):
    answerPath = pvPath + "/answer"
    if os.path.exists(answerPath):
        shutil.copytree(answerPath, userPath)


def getTargetFile(port, language):
    pod = redisTool.getPodByPort(port)
    filePath = pod.pvPath + "/answer/main." + language
    with open(filePath, mode="r", encoding="utf-8") as f:
        text = f.read()
    return text
