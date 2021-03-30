---
title: "k8s in action(03) - deploying your first app"
date: 2021-01-15T23:11:31+08:00
draft: false
tags: ["k8s"]
---



## 3.1 安装k8s集群

1. 使用云厂商提供的k8s服务

2. kubeadm(https://github.com/kubernetes/kubeadm)

3. 使用Docker Desktop（mac，win）

4. 使用minikube(http://github.com/kubernetes/minikube)

   ```bash
   # 运行
   # 启动时指定国内镜像minikube start --image-mirror-country='cn' --image-repository='registry.cn-hangzhou.aliyuncs.com/google_containers'
   minikube start
   # 状态
   minikube status
   # 登录
   minikube ssh
   ```

5. 使用kind(不成熟，不推荐)

6. 最复杂的方法(https://github.com/kelseyhightower/Kubernetes-the-hard-way)

## 3.2 与k8s集群交互

### 下载kubectl

1. 下载kubectl(https://github.com/kubernetes/kubectl)

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210319170111.png)

2. 添加别名：

```bash
# .zshrc
alias k=kubectl
```

3. 自动补全：

```bash
source <(kubectl completion bash)
complete -o default -F __start_kubectl k
```

4. 配置文件`~/.kube/config`



### 使用kubectl

```bash
# 获取集群信息
kubectl cluster-info
# 查看nodes
kubectl get nodes
# node详情
k describe nodes minikube
```



### dashboard

```bash
minikube dashboard
```



## 3.3 运行应用

使用命令行创建deployment

```bash
kubectl create deployment kubia --image=qiaocc/kubia:1.0
```

查看deployment:

```bash
kubectl get deployments
```

你可能想要查看container的状态:

```bash
kubectl get containers
```

返回报错, error: the server doesn't have a resource type "containers"

实际上，在k8s中没有container类型， container不是k8s中最小的单元。

### Pod

在Kubernetes中，不是部署单个容器，而是部署一组位于同一位置的容器，即所谓的pod。

特点：

- 一组密切关联的容器
- 在同一个节点运行
- 共享Linux namespace

我们可以认为，每个pod是一个独立的物理机。

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210325164011.png)

查看pod：

```bash
kubectl get pods
```

查看详情：

```bash
kubectl describe pod
```



运行kubectl create后，k8s在背后做了什么事情？

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210325164957.png)

执行`kubectl create`命令时，会先想api server发送一个http请求， 说明我要创建一个deployment了。k8s创建Pod对象（这时候，只是创建对象，还没有真正创建pod）。然后将pod对象调度到工作节点，节点上的kubelete会指导Docker创建对应的容器。



### 暴露应用

应用已经跑起来了，如何访问这个服务呢？每个pod有独立的ip，但是这个ip只能通过集群内部访问。如何在集群外部访问呢？

一种办法是，创建Service，指定类型是LoadBalancer。

```bash
kubectl expose deployment kubia --type=LoadBalancer --port 8080
```

这个命令会：

- 把所有属于kubia的pod，作为服务暴露出去。
- 外部用户通过负载均衡访问

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210326185205.png)

查看刚刚创建的服务:

```bash
kubectl get service
```



创建服务的流程：

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210330143857.png)

其中， 第3步，k8s本身不提供负载均衡。如果你的集群在云上部署，他会使用云厂商的负载均衡。

当`EXTERNAL-IP`状态从pending改为真正的ip后， 就可以使用curl命令访问：

```bash
curl 35.246.179.22:8080
```

注意：minikube不支持这种方式。

minikube如何访问服务呢？

```bash
minikube service kubia --url
```



### 水平扩展

现在我们运行了一个单实例的应用。如果突然有很多人访问应用，那么单实例就抗不住大量的流量。这时候，你需要额外的实例，去分担整个流量。这就是水平扩展。

```bash
kubectl scale deployment kubia --replicas=3
```

你只需要告诉k8s，最终想要达到的效果是， 有3个kubia的副本。k8s就会自动扩展。

这是k8s中的一个基础原则。你只要告诉k8s，最终想实现的效果，k8s就会去实现它。你不用关心k8s如何实现的。k8s会自动检查当前状态，和最终实现的状态，它们两者的差异，最终会决定如何实现它。

```bash
$ k get deployments
NAME    READY   UP-TO-DATE   AVAILABLE   AGE
kubia   3/3     3            3           4h56m
```

3个实例已经up-to-date, 已经ready。

我们查看一下pod的信息：

```bash
$ k get pods
NAME                     READY   STATUS    RESTARTS   AGE
kubia-5bd75b8fdd-ch24v   1/1     Running   0          10m
kubia-5bd75b8fdd-kd49l   1/1     Running   0          5h1m
kubia-5bd75b8fdd-l8g5j   1/1     Running   0          10m
```

所有pod都已经ready，状态是Running。

如果你运行的是单节点集群， 那么所有pod都在同一个节点。

如果是多节点集群， 怎么查看pod位于哪个节点呢？

```bash
k get pods -o wide
```



多运行几次，观察一下响应：

```bash
$ curl 35.246.179.22:8080
```

我们会发现， 请求由不同的pod来处理。

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210330164903.png)