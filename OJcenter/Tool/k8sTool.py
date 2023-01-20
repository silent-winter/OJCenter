import os
import shutil
from retry import retry

from kubernetes import client
from kubernetes.client import V1Pod, V1PodList, V1PersistentVolumeClaim
from kubernetes.client.rest import ApiException

from OJcenter.Tool import aesTool, timeTool
from OJcenter.Tool.model import PodMetaInfo

# 获取apiserver token
# kubectl -n kubernetes-dashboard get secret $(kubectl -n kubernetes-dashboard get sa/admin-user -o jsonpath="{.secrets[0].name}") -o go-template="{{.data.token | base64decode}}"
# api文档
# https://github.com/kubernetes-client/python/blob/master/kubernetes/docs
token = 'eyJhbGciOiJSUzI1NiIsImtpZCI6InJZVzRWdWZjOXNpdENJcl82Sm5BblhuRVVjUjlRMlJYQ3E3M3pKNlVsVEkifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlcm5ldGVzLWRhc2hib2FyZCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhZG1pbi11c2VyLXRva2VuLXd6YzRkIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImFkbWluLXVzZXIiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiJiNGEzODcxOC1lZTJlLTRjZTYtODcxMi04ZTE3OWEzYmE2NjIiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZXJuZXRlcy1kYXNoYm9hcmQ6YWRtaW4tdXNlciJ9.IKQD-Ei1DcSCXz3SA-EwvQBQRObuSmTqnsQqadmfK0Y79wvQHM1Yuq8c6aWjvrmT18o5UdZ7yrfyWBeN2SzPDaR2FazbK4MDiRoUG7rhtwOYo19RZ3e_RlYzxjjq3h7Cd2PSfryU1zYQQi1INiZvXpIE45W0_WSmUGzSZTl4dStiSBiVvpRZduq2_7A-LKoXG_UwVkiCV0TR7NXp3W8sMQ8jCdEBa0skZ_1DRHd4yg9NoPE6NjaZPa2U0Ol8hc2tzt_yQFjX1iC4n_RtaPZBXp2i5R8LmpbhY2Dw-2VVc01r9i2iBTR5xaMWh75Pt_YsGPqyyBKu_adPklKMuE2Rog'
apiServer = 'https://192.168.149.133:6443'

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
# @PodMetaInfo(ip, port, podName, pvPath)
_result = []


def init():
    global _port
    start, end = 9100, 9102
    _port = start
    create(end - start + 1)


# 创建n个pod
def create(n):
    global _port
    for i in range(_port, _port + n):
        pvcName = "pvc-%s" % i
        podName = "server-%s" % i
        create_pvc(pvcName)
        create_pod(podName, i, pvcName)
        pvName = get_pv_name(pvcName)
        # 初始化文件
        pvPath = "/nfs/data/default-%s-%s" % (pvcName, pvName)
        shutil.copytree("/nfs/data/base/.vscode", pvPath + "/.vscode")
        shutil.copytree("/nfs/data/base/answer", pvPath + "/answer")
        shutil.copytree("/nfs/data/base/test", pvPath + "/test")
        _result.append(PodMetaInfo(get_host_ip(podName), i, podName, pvPath))
    # time.sleep(2)
    # _index = _index - n
    # for i in range(_port, _port + n):
    #     podName = "server-%s" % _index
    #     _index = _index + 1
    #     _result.append(PodMetaInfo(get_host_ip(podName), i, podName, "/nfs/data/" + pvName))
    #     print(podName, "create success!")
    print(_result)
    _port = _port + n


def select():
    return _result.pop()


def create_pod(podName, hostPort, pvcName) -> V1Pod:
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
      nodeName: k8s-worker1（可选）
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


def delete_pod(name, namespace) -> V1Pod:
    try:
        return coreApi.delete_namespaced_pod(name, namespace)
    except ApiException as e:
        print("Exception when calling CoreV1Api->delete_namespaced_pod: %s\n" % e)


def create_pvc(pvcName) -> V1PersistentVolumeClaim:
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


@retry(tries=5, delay=1)
def get_pv_name(pvcName):
    try:
        pvc = coreApi.read_namespaced_persistent_volume_claim(name=pvcName, namespace="default")
        pvName = pvc.to_dict().get("spec").get("volume_name")
        assert pvName is not None
        return pvName
    except ApiException as e:
        print("Exception when calling CoreV1Api->read_namespaced_persistent_volume_claim: %s\n" % e)
        return ""


@retry(tries=5, delay=1)
def get_host_ip(podName):
    try:
        pod = coreApi.read_namespaced_pod(name=podName, namespace="default")
        hostIp = pod.to_dict().get("status").get("host_ip")
        assert hostIp is not None
        return hostIp
    except ApiException as e:
        print("Exception when calling CoreV1Api->read_namespaced_pod: %s\n" % e)
        return ""


def list_pod_for_all_namespaces() -> V1PodList:
    podList = coreApi.list_pod_for_all_namespaces(watch=False)
    print("Listing pods with their IPs:")
    for item in podList.items:
        print("%s\t%s\t%s" % (item.status.pod_ip, item.metadata.namespace, item.metadata.name))
    return podList


def copy_permanent_folder(username, pvPath):
    userPath = "/dockerdir/userfolder/%s/answer" % username
    shutil.rmtree(pvPath + "/answer")
    shutil.copytree(userPath, pvPath + "/answer")
    currTime = timeTool.getCurrTime()
    authFile = "/dockerdir/userfolder/%s/authorization" % username
    if os.path.exists(authFile):
        os.remove(authFile)
    code = aesTool.getEncrypt(username + ' ' + currTime)
    with open(file=authFile, mode="w") as f:
        f.write(code.decode())
    shutil.copyfile(authFile, pvPath + "/.vscode/authorization")


def backup_answer(userPath, pvPath):
    shutil.copytree(pvPath + "/answer", userPath)


init()
