---
title: "k8s in action(02) - understanding containers"
date: 2021-01-02T13:51:15+08:00
draft: false
tags: ["k8s"]
---

入门

```bash
minikube version
# 运行k8s集群
minikube start

kubectl version
# 查看集群信息
kubectl cluster-info
# 查看节点信息
kubectl get nodes
```



# 配置k8s集群

方法:

1. minikube 单节点
2. kubeadm 多节点

## 使用minikube搭建

1. 安装minikube `https://github.com/kubernetes/minikube`

2. 启动时设置国内镜像`minikube start --image-mirror-country='cn' --image-repository='registry.cn-hangzhou.aliyuncs.com/google_containers'`

   结果：

   ```
   😄  Debian 10.6 上的 minikube v1.17.0
   ✨  根据现有的配置文件使用 docker 驱动程序
   👍  Starting control plane node minikube in cluster minikube
   🚜  Pulling base image ...
   🔥  Creating docker container (CPUs=2, Memory=3900MB) ...
   🐳  正在 Docker 20.10.2 中准备 Kubernetes v1.20.2…
       ▪ Generating certificates and keys ...
       ▪ Booting up control plane ...
       ▪ Configuring RBAC rules ...
   🔎  Verifying Kubernetes components...
   🌟  Enabled addons: storage-provisioner, default-storageclass
   🏄  Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default

   ```



3. 安装kubectl

# chap2 使用docker和k8s



## 2.3 在k8s运行第一个应用

创建deployment

```
k create deployment kubia --image=qiaocc/node-server
```

注意

```bash
# 运行老的命令会报错
k create deployment node-pod --image=qiaocc/node-server --port 8080 --generator=run/v1

# 报错
Flag --generator has been deprecated, has no effect and will be removed in the future.
```

获取deployment:

```
k get deployments
```

创建deployment后, 会默认创建pod.

pod内部的容器, 共享相同的ip, hostname和命名空间等, 可以理解为容器们在"同一台机器"

```
查看pod信息:
k get pods

# pod详情
k describe pod <pod名>
```

创建deployment背后发生了什么?

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210208150519.png)

### 创建服务

为了访问到app, 我们要创建**LoadBalancer Service**(负载均衡服务)

```bash
k expose deployment kubia --type=LoadBalancer --port=8080
```

这个命令将deployment下的所有pod都暴露出来. 你在访问时, 会通过负载均衡连接到集群.

查看所有api:

```bash
kubectl api-resources
```

如何理解负载均衡服务?

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210208150520.png)

查看服务状态:

```
k get service

NAME    TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
kubia   LoadBalancer   10.108.32.94   <pending>     8080:31820/TCP   90m
```

k8s的负载均衡服务, 是基于云厂商的基础设施的. 如果在本地使用k8s服务, 由于没有云厂商的基础设施, 无法自动创建负载均衡服务. 所以我们需要换一种方式去获取服务.

```
minikube service kubia --url
# http://192.168.49.2:31820
```



### 水平扩展

```
k scale deployment kubia --replicas 3
```

扩展后, 可以看到deployment的结果:

```
k get deployments
NAME    READY   UP-TO-DATE   AVAILABLE   AGE
kubia   3/3     3            3           11h

```



```
kubectl get pods
                  		 READY   STATUS    RESTARTS   AGE
kubia-64bf794997-95c5q   1/1     Running   0          110s
kubia-64bf794997-b6pr4   1/1     Running   0          110s
kubia-64bf794997-v9dcn   1/1     Running   1          7h38m
```



创建了三个容器, 这三个容器, 来自不同的pod. 因为我们使用的是minikube, 所有的pod都来自同一个node节点.

```
k get nodes -o wide
NAME                     READY   STATUS    RESTARTS   AGE    IP           NODE       NOMINATED NODE   READINESS GATES
kubia-64bf794997-95c5q   1/1     Running   0          4h5m   172.17.0.7   minikube   <none>           <none>
kubia-64bf794997-b6pr4   1/1     Running   0          4h5m   172.17.0.8   minikube   <none>           <none>
kubia-64bf794997-v9dcn   1/1     Running   1          11h    172.17.0.6   minikube   <none>           <none>

```

可以看到, 三个pod都来自minikube节点.

每个pod被分配的节点并不重要, 我们不需要关心.

