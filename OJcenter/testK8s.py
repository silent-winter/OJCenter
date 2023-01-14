from kubernetes import client, config
from kubernetes.client.rest import ApiException


def main():
    # 获取apiserver token
    # kubectl -n kubernetes-dashboard get secret $(kubectl -n kubernetes-dashboard get sa/admin-user -o jsonpath="{.secrets[0].name}") -o go-template="{{.data.token | base64decode}}"
    # api文档
    # https://github.com/kubernetes-client/python/blob/master/kubernetes/docs
    token = 'eyJhbGciOiJSUzI1NiIsImtpZCI6InJZVzRWdWZjOXNpdENJcl82Sm5BblhuRVVjUjlRMlJYQ3E3M3pKNlVsVEkifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlcm5ldGVzLWRhc2hib2FyZCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhZG1pbi11c2VyLXRva2VuLXd6YzRkIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImFkbWluLXVzZXIiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiJiNGEzODcxOC1lZTJlLTRjZTYtODcxMi04ZTE3OWEzYmE2NjIiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZXJuZXRlcy1kYXNoYm9hcmQ6YWRtaW4tdXNlciJ9.IKQD-Ei1DcSCXz3SA-EwvQBQRObuSmTqnsQqadmfK0Y79wvQHM1Yuq8c6aWjvrmT18o5UdZ7yrfyWBeN2SzPDaR2FazbK4MDiRoUG7rhtwOYo19RZ3e_RlYzxjjq3h7Cd2PSfryU1zYQQi1INiZvXpIE45W0_WSmUGzSZTl4dStiSBiVvpRZduq2_7A-LKoXG_UwVkiCV0TR7NXp3W8sMQ8jCdEBa0skZ_1DRHd4yg9NoPE6NjaZPa2U0Ol8hc2tzt_yQFjX1iC4n_RtaPZBXp2i5R8LmpbhY2Dw-2VVc01r9i2iBTR5xaMWh75Pt_YsGPqyyBKu_adPklKMuE2Rog'
    apiserver = 'https://192.168.149.133:6443'

    configuration = client.Configuration()
    setattr(configuration, 'verify_ssl', False)
    client.Configuration.set_default(configuration)
    configuration.host = apiserver
    configuration.verify_ssl = False
    configuration.debug = True
    configuration.api_key = {"authorization": "Bearer " + token}
    client.Configuration.set_default(configuration)

    v1 = client.CoreV1Api(client.ApiClient(configuration))
    # nodes = v1.list_node(watch=False)
    # for i in nodes.items:
    #     print("Node .....")
    #     print(i)

    pods = v1.list_pod_for_all_namespaces(watch=False)
    for i in pods.items:
        print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))

    # pvc = v1.list_persistent_volume_claim_for_all_namespaces()
    # for i in pvc.items:
    #     print("PVC .....")
    #     print(i)
    # ret = v1.list_namespaced_pod("kube-system")
    # list_pod_for_all_namespaces(v1)

    # create_namespace(v1)
    # delete_namespace(v1)
    # list_namespace(v1)
    # create_namespaced_deployment(configuration)
    # update_namespaced_deployment(configuration)
    # delete_namespaced_deployment(configuration)
    # create_namespaced_service(v1)
    # delete_namespaced_service(v1)
    # delete_namespaced_pod(v1)
    create_namespaced_pod(v1)


def list_pod_for_all_namespaces(v1):
    ret = v1.list_pod_for_all_namespaces(watch=False)
    print("Listing pods with their IPs:")
    for i in ret.items:
        print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))


def create_namespace(v1):
    bodynamespace = {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {
            "name": "test123",
        }
    }
    ret = v1.create_namespace(body=bodynamespace)
    print("create_namespace result")
    print(ret)


def delete_namespace(v1):
    body = client.V1DeleteOptions()
    body.api_version = "v1"
    body.grace_period_seconds = 0
    ret = v1.delete_namespace("test123", body=body)
    print("delete_namespace result")
    print(ret)


def list_namespace(v1):
    limit = 56  # 返回最大值,可选参数可以不写
    timeout_seconds = 56  # 超时时间可选参数
    watch = False  # 监听资源，可选参数可以不填
    try:
        api_response = v1.list_namespace(limit=limit, timeout_seconds=timeout_seconds, watch=watch)
        print("list_namespace result")
        for namespace in api_response.items:
            print(namespace.metadata.name)
    except ApiException as e:
        print("Exception when calling CoreV1Api->list_namespace: %s\n" % e)


def create_namespaced_deployment(configuration):
    v1 = client.AppsV1Api(client.ApiClient(configuration))
    # http://www.json2yaml.com/ 把yaml转成json ；然后用https://www.json.cn/json/jsonzip.html 压缩json
    '''
    apiVersion: apps/v1
    kind: Deployment
    metadata: 
    name: test1
    spec:
    selector: 
        matchLabels:
        app: test
    replicas: 1
    template:
        metadata:
        labels: 
            app: test
        spec:
        containers:
            - name: test 
            image: nginx:latest 
            imagePullPolicy: IfNotPresent 
            ports:
                - containerPort: 80
    '''
    body = eval(
        '{"apiVersion":"apps/v1","kind":"Deployment","metadata":{"name":"test1"},"spec":{"selector":{"matchLabels":{'
        '"app":"test"}},"replicas":1,"template":{"metadata":{"labels":{"app":"test"}},"spec":{"containers":[{'
        '"name":"test","image":"nginx:latest","imagePullPolicy":"IfNotPresent","ports":[{"containerPort":80}]}]}}}}')
    resp = v1.create_namespaced_deployment(body=body, namespace="default")
    print("create_namespaced_deployment result")
    print(resp)


def update_namespaced_deployment(configuration):
    v1 = client.AppsV1Api(client.ApiClient(configuration))
    body = eval(
        '{"apiVersion":"apps/v1","kind":"Deployment","metadata":{"name":"test1"},"spec":{"selector":{"matchLabels":{'
        '"app":"test"}},"replicas":2,"template":{"metadata":{"labels":{"app":"test"}},"spec":{"containers":[{'
        '"name":"test","image":"nginx:latest","imagePullPolicy":"IfNotPresent","ports":[{"containerPort":80}]}]}}}}')
    resp = v1.patch_namespaced_deployment(name="test1", namespace="default", body=body)
    print("patch_namespaced_deployment result")
    print(resp)


def delete_namespaced_deployment(configuration):
    v1 = client.AppsV1Api(client.ApiClient(configuration))
    body = client.V1DeleteOptions(propagation_policy='Foreground', grace_period_seconds=0)
    resp = v1.delete_namespaced_deployment(name="test1", namespace="default", body=body)
    print("delete_namespaced_deployment result")
    print(resp)


def create_namespaced_service(v1):
    namespace = "default"
    body = {'apiVersion': 'v1', 'kind': 'Service', 'metadata': {'name': 'nginx-service', 'labels': {'app': 'nginx'}},
            'spec': {'ports': [{'port': 80, 'targetPort': 80}], 'selector': {'app': 'nginx'}}}
    try:
        api_response = v1.create_namespaced_service(namespace, body)
        print(api_response)
    except ApiException as e:
        print("Exception when calling CoreV1Api->create_namespaced_service: %s\n" % e)


def delete_namespaced_service(v1):
    name = 'nginx-service'  # 要删除svc名称
    namespace = 'default'  # 命名空间
    try:
        api_response = v1.delete_namespaced_service(name, namespace)
        print(api_response)
    except ApiException as e:
        print("Exception when calling CoreV1Api->delete_namespaced_service: %s\n" % e)


def create_namespaced_pod(v1):
    # http://www.json2yaml.com/ 把yaml转成json ；然后用https://www.json.cn/json/jsonzip.html 压缩json
    """
    apiVersion: v1
    kind: Pod
    metadata:
      namespace: default
      name: ojK8sServer
      labels:
        app: ojK8sServer
    spec:
      containers:
        - name: ojK8sServer
          image: server_20220330:latest
          ports:
            - containerPort: 8443
    """
    body = eval(
        '{"apiVersion":"v1","kind":"Pod","metadata":{"namespace":"default","name":"oj-k8s-server","labels":{"app":"oj-k8s-server"}},"spec":{"nodeSelector":{"role":"worker1"},"containers":[{"image":"server_20220330:latest","imagePullPolicy":"IfNotPresent","name":"server","ports":[{"containerPort":8443,"hostPort":9100}]}]}}')
    resp = v1.create_namespaced_pod(body=body, namespace="default")
    print("create_namespaced_pod result")
    print(resp)


def delete_namespaced_pod(v1):
    try:
        api_response = v1.delete_namespaced_pod("oj-k8s-server", "default")
        print(api_response)
    except ApiException as e:
        print("Exception when calling CoreV1Api->delete_namespaced_pod: %s\n" % e)


if __name__ == '__main__':
    main()
