## 基于Kubernetes的VSCode-OJ云编程环境

#### 后端访问逻辑：
![后端访问逻辑图](https://vscode-oj.oss-cn-beijing.aliyuncs.com/process.png) 

#### 文件挂载：
![文件挂载图](https://vscode-oj.oss-cn-beijing.aliyuncs.com/NFS%26PV.png) 

#### 节点亲和性，控制每台机器Code-Server部署上限：
![节点亲和性图](https://vscode-oj.oss-cn-beijing.aliyuncs.com/nodeAffinity.png) 

#### deployment的yaml定义：
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: server-10000
  labels:
    app: oj-k8s-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: oj-k8s-server
      id: "10000"
  template:
    metadata:
      namespace: default
      name: server-%s
      labels:
        app: oj-k8s-server
        id: "10000"
    spec:
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - preference:
                matchExpressions:
                  - key: node2/vscode-limit
                    operator: Gt
                    values: ["0"]
              weight: 4
            - preference:
                matchExpressions:
                  - key: node3/vscode-limit
                    operator: Gt
                    values: ["0"]
              weight: 5
      initContainers:
        - name: init-server
          image: server_20230323:latest
          imagePullPolicy: IfNotPresent
          command: ["/bin/sh", "-c", "cp -R /config/workspace/. /mnt"]
          volumeMounts:
            - name: shared-workspace
              mountPath: "/mnt"
      containers:
        - name: server
          image: server_20230323:latest
          imagePullPolicy: IfNotPresent
          lifecycle:
            postStart:
              exec:
                command: ["/bin/sh", "-c", "cp -R /mnt/. /config/workspace"]
          ports:
            - name: vscode
              containerPort: 8443
          volumeMounts:
            - name: shared-workspace
              mountPath: "/mnt"
            - name: workspace-volume
              mountPath: "/config/workspace"
          resources:
            limits:
              cpu: "500m"
              memory: "512Mi"
            requests:
              cpu: "30m"
              memory: "300Mi"
      volumes:
        - name: shared-workspace
          emptyDir: {}
        - name: workspace-volume
          persistentVolumeClaim:
            claimName: pvc-10000
```
spec.affinity.nodeAffinity.preferredDuringSchedulingIgnoredDuringExecution.preference[]用于设置节点亲和性；node2/vscode-limit是节点上的标签；values: ["%s"]是动态传入的值，表示此时该节点上部署的Code-Server的个数。

initContainers[]用于初始化工作目录，引用了一个emptyDir挂载，与主容器共享/mnt目录，将/config/workspace/下的文件暂存到/mnt下。

containers[]中定义了一个postStart，将共享目录/mnt下的内容重新复制到工作目录下；在resources中定义了内存和CPU资源限制；定义了PVC挂载。

#### Service的yaml定义：
```yaml
apiVersion: v1
kind: Service
metadata:
  name: svc-10000
  labels:
    app: oj-svc
spec:
  selector:
    app: oj-k8s-server
    id: 10000
  type: ClusterIP
  ports:
  - name: http
    port: 10000
    targetPort: 8443
```
Service type定义为ClusterIP，只能在集群内部通过虚拟ip访问Pod；selector中通过id匹配Pod。