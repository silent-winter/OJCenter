import os
import shutil
from typing import Optional

from retry import retry

from kubernetes import client
from kubernetes.client import V1Pod, V1PodList, V1PersistentVolumeClaim
from kubernetes.client.rest import ApiException

from OJcenter.Tool import aesTool, timeTool, redisTool
from OJcenter.Tool.model import PodMetaInfo

# 获取apiserver token
# kubectl -n kubernetes-dashboard get secret $(kubectl -n kubernetes-dashboard get sa/admin-user -o jsonpath="{.secrets[0].name}") -o go-template="{{.data.token | base64decode}}"
# api文档
# https://github.com/kubernetes-client/python/blob/master/kubernetes/docs
token = 'eyJhbGciOiJSUzI1NiIsImtpZCI6InplR3dYNXRsbW80bmRJaU82bS1OSE8weXdJRDlHMDN0d2RzUDJ5WGg1SDgifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlcm5ldGVzLWRhc2hib2FyZCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhZG1pbi11c2VyLXRva2VuLWs3OTZzIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImFkbWluLXVzZXIiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiIzOTdjNzY5NS0xZDdhLTRmZmQtOTZlMi00NTkxNTNkOWI4OTIiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZXJuZXRlcy1kYXNoYm9hcmQ6YWRtaW4tdXNlciJ9.cNx9hshVWHoZHjK5ZF0HCCf7xh4sb4YIW4thbIC6Z8HfFi-W4DkTQoh5AnFbv9_DY8zllydsg8AcOobZvNLiGh2F-LFizETdmZ8NUh6o2QQhrXxsidcorl9zSZb-8CbqBgzTGqj1_KNXRptdORxk_PAVuQVDyKPdePnYkkMGgYxlNlXcOsZZEUXjDC5zHdpTZupR7ZXYCN92RKqwDIjE1hMzBwEsdK0xFFZ0P9t_UOec95Bp_n3wSO2XLhuJdrxCQX69o2NikCZz-XjiZJbSAMjJMC-EeIVSaxjHs2orkBhzSdh8nf1dmCRl2JP3wYIZiy4VdgeDXZyOnHITbMH1BA'
apiServer = 'https://202.4.155.97:6443'

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
_maxPort = 50000
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
    podName = "server-%s" % port
    createPvc(pvcName)
    createPod(podName, port, pvcName)
    pvName = getPvName(pvcName)
    # 初始化文件
    pvPath = "/nfs/data/default-%s-%s" % (pvcName, pvName)
    os.system("cp -rp /nfs/data/base/.vscode " + pvPath)
    os.system("cp -rp /nfs/data/base/answer " + pvPath)
    os.system("cp -rp /nfs/data/base/test " + pvPath)
    return PodMetaInfo(getHostIp(podName), port, podName, pvPath)


def createPod(podName, hostPort, pvcName) -> V1Pod:
    # http://www.json2yaml.com/ yaml转json
    # https://www.json.cn/json/jsonzip.html 压缩json
    """
    apiVersion: v1
    kind: Pod
    metadata:
      namespace: default
      name: server-1
      labels:
        app: oj-k8s-server
    spec:
      containers:
        - name: server-1
          image: server_20220330:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8443
              hostPort: 10000
          volumeMounts:
            - name: answer-volume
              mountPath: "/config/workspace"
          resources:
            limits:
              cpu: "1"
              memory: "1Gi"
            requests:
              cpu: "0.5"
              memory: "512Mi"
      volumes:
        - name: answer-volume
          persistentVolumeClaim:
           claimName: pvc-1
    """
    body = eval(
        '{"apiVersion":"v1","kind":"Pod","metadata":{"namespace":"default","name":"' + podName + '","labels":{"app":"oj-k8s-server"}},"spec":{"containers":[{"name":"' + podName + '","image":"server_20220330:latest","imagePullPolicy":"IfNotPresent","ports":[{"containerPort":8443,"hostPort":' + str(
            hostPort) + '}],"volumeMounts":[{"name":"answer-volume","mountPath":"/config/workspace"}]}],"volumes":[{"name":"answer-volume","persistentVolumeClaim":{"claimName":"' + pvcName + '"}}]}}')
    pod = coreApi.create_namespaced_pod(body=body, namespace="default", async_req=False)
    return pod


def deletePod(name) -> V1Pod:
    try:
        return coreApi.delete_namespaced_pod(name, "default")
    except ApiException as e:
        print("Exception when calling CoreV1Api->delete_namespaced_pod: %s\n" % e)


def createPvc(pvcName) -> V1PersistentVolumeClaim:
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
        pvName = pvc.to_dict().get("spec").get("volume_name")
        assert pvName is not None
        return pvName
    except ApiException as e:
        print("Exception when calling CoreV1Api->read_namespaced_persistent_volume_claim: %s\n" % e)
        return ""


@retry(tries=5, delay=1)
def getHostIp(podName):
    try:
        pod = coreApi.read_namespaced_pod(name=podName, namespace="default")
        hostIp = pod.to_dict().get("status").get("host_ip")
        assert hostIp is not None
        return hostIp
    except ApiException as e:
        print("Exception when calling CoreV1Api->read_namespaced_pod: %s\n" % e)
        return ""


def listPodForAllNamespaces() -> V1PodList:
    podList = coreApi.list_pod_for_all_namespaces(watch=False)
    print("Listing pods with their IPs:")
    for item in podList.items:
        print("%s\t%s\t%s" % (item.status.pod_ip, item.metadata.namespace, item.metadata.name))
    return podList


def isPodExist(podName):
    podList = coreApi.list_namespaced_pod(field_selector=f'metadata.name={podName}', namespace="default")
    return len(podList.items) == 1


def copyPermanentFolder(username, pvPath):
    userPath = "/dockerdir/userfolder/%s/answer" % username
    shutil.rmtree(pvPath + "/answer")
    shutil.copytree(userPath, pvPath + "/answer")
    # 设置文件所有者
    os.system("chown -R 911 %s/answer" % pvPath)
    os.system("chgrp -R 911 %s/answer" % pvPath)
    currTime = timeTool.getCurrTime()
    authFile = "/dockerdir/userfolder/%s/authorization" % username
    if os.path.exists(authFile):
        os.remove(authFile)
    code = aesTool.getEncrypt(username + ' ' + currTime)
    with open(file=authFile, mode="w") as f:
        f.write(code.decode())
    shutil.copyfile(authFile, pvPath + "/.vscode/authorization")


def backupAnswer(userPath, pvPath):
    shutil.copytree(pvPath + "/answer", userPath)


def getTargetFile(port, language):
    pod = redisTool.getPodByPort(port)
    filePath = pod.pvPath + "/answer/main." + language
    with open(filePath, mode="r", encoding="utf-8") as f:
        text = f.read()
    return text
