---
title: "k8s-in-action笔记-05-running-app-in-k8s"
date: 2021-02-02T23:11:31+08:00
draft: false
categories: ["k8s"]
---



# chap5 Running Apps in Pods

## 重点

- 理解如何创建和何时创建group containers
- 用yaml文件创建pod，运行app
- 与app交互，查看log和运行环境
- 扩展主容器，增加sidecar容器
- pod启动时，初始化容器





## 5.1 理解pod

### 5.1.1 pod的特点：

1. 一个pod可能包含一个或多个container
2. 一个pod只能属于单个node，不会属于多个node

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210208150504.png)



#### 为什么需要pod？

假设一个应用，包含多个进程，进程间是通过ipc或shared files通信的，这就要求多个进程运行在同一台电脑上。

一个容器也可以运行多个进程，但是不建议这样做。原因是：

1. 无法区分不同进程的日志。默认情况下，应用将日志写到标准输出，docker可以很方便的查看日志，但是如果一个容器运行多个进程，那就无法区分日志属于哪个进程的。
2. 容器在根进程死亡时会自动重启，不会管子进程的状态。

既然不建议在一个容器中运行多个进程，那么我们就要把多个进程，拆分到多个容器中，并且保证多个进程好像在同一个容器运行。这就需要引入pod了。

pod内的容器共享同一份网络空间，例如网络接口，ip，端口。

pod内的容器，同时也共享hostname。

但是不会共享文件系统，如果想要共享文件系统，需要单独挂载。

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210208150505.png)

基于上述的特点，多个进程虽然运行在不同的容器中，但是他们好像在同一个容器一样。



### 5.1.2 Organizing containers into pods

在虚拟机时代，一台虚拟机可能运行多个应用。但是在使用pod时，建议的做法是一个pod只运行一个app。app的每个进程，运行在不同的容器里。

为什么不建议多个应用运行在同一个pod？

1. 提高资源利用率。如果有多个节点，但是应用只跑在一个节点，其他节点资源（cpu、内存、磁盘，带宽）就浪费了
2. 方便水平扩展。水平扩展的最小单位是一个pod，假设前端应用和数据库部署在同一个pod，扩展时，会同时扩展app和数据库，但是通常数据库的扩展方法和前端是不同的。前端是无状态的，但是数据库是有状态的，扩展可能要考虑更多因素。

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210208150506.png)

#### sidecar 容器

运行在同一个pod的多个进程中，有的是主容器，负责主要任务。除此之外，还有**sidecar容器**，负责辅助性的任务。

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210208150507.png)



是否需要把容器分到多个pod？如果下面几个判断条件都回答“是”，那么不要拆分到多个pod。

1. 这些容器需要运行在同一个host吗？
2. 是否想把这些容器当做一个整理来管理？
3. 它们是一个整体吗？
4. 它们可以一起水平扩展吗？
5. 单个节点能满足它们的资源组合需求吗？

经验法则：总是把容器放到不同的pod中，除非有特殊的原因需要把它们作为一个整体。



## 5.2 通过yaml配置文件创建pod

前面的章节中，我们已经学会使用命令行创建pod。这一章我们来学习使用配置文件创建pod，方便管理。



```yaml
# kubia.yaml
apiVersion: v1 # api版本
kind: Pod # 类型
metadata:
  name: node-pod # pod名称
spec:
  containers:
    - name: node-server-container # 容器名称
      image: qiaocc/node-server:latest # 镜像
      ports:
        - containerPort: 8080 # app监听端口
```

这份配置文件结构整齐，更加容易理解。

**运行**：

```bash
# 运行
kubectl apply -f kubia.yaml

# 查看pod状态, -o wide 查看更多， -o yaml输出yaml格式
kubectl get pod node-pod

# 查看pod详情
kubectl describe pod node-pod

# 查看创建pod时，发生的事件
kubectl get events
```

如果配置文件有更新，重新运行`kubectl apply`命令。