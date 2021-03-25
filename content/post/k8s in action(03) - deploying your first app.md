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



原理

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210325164957.png)