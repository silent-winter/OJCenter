import time
import urllib3

from kubernetes import client

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
start, end = 30011, 30030


if __name__ == '__main__':
    """
    apiVersion: v1
    kind: Service
    metadata:
      name: svc-1
      labels:
        app: oj-svc
    spec:
      selector:
        app: oj-k8s-server
        id: "1"
      type: NodePort
      ports:
      - name: http
        port: 30000
        targetPort: 8443
        nodePort: 30000
    """
    for i in range(start, end + 1):
        body = eval(
            '{"apiVersion":"v1","kind":"Service","metadata":{"name":"svc-%s","labels":{"app":"oj-svc"}},"spec":{"selector":{"app":"oj-k8s-server","id":"%s"},"type":"NodePort","ports":[{"name":"http","port":%s,"targetPort":8443,"nodePort":%s}]}}' % (
                i, i, i, i)
        )
        coreApi.create_namespaced_service(namespace="default", body=body)
