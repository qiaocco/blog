---
title: "k8s in action(05) - running app in k8s"
date: 2021-02-02T23:11:31+08:00
draft: false
tags: ["k8s"]
---



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
  name: kubia # pod名称
spec:
  containers:
    - name: kubia # 容器名称
      image: qiaocc/kubia:0.1 # 镜像
      ports:
        - containerPort: 8080 # app监听端口
```

这份配置文件结构整齐，更加容易理解。

**运行**：

```bash
# 运行
kubectl apply -f kubia.yaml

# 查看pod状态, -o wide 查看更多， -o yaml输出yaml格式
kubectl get pod kubia

# 查看pod详情
kubectl describe pod kubia

# 查看创建pod时，发生的事件
kubectl get events
```

如果配置文件有更新，重新运行`kubectl apply`命令。



## 5.3 与app和pod进行交互

### 5.3.1 向pod中的应用发送请求

#### 方法一：登录到node，发送请求

1. 获取pod的ip

   ```bash
   kubectl get pod kubia -o wide
   # output
   NAME    READY   STATUS    RESTARTS   AGE    IP           NODE       NOMINATED NODE   READINESS GATES
   kubia   1/1     Running   2          6d2h   172.17.0.8   minikube   <none>           <none>
   ```

   输出结果显示，kubia pod的ip是`172.17.0.8`

   在k8s中，同一个node的不同pod之间可以联通，不通node的不同pod也可以联通

2.  ssh登录pod所在的node，发起请求。

   ```
   minikubt ssh
   curl 172.17.0.8:8000
   ```

应用场景：出现连接问题时，这种方法是结局问题的最短路径。



#### 方法二：从一次性的pod连接

```bash
kubectl run --image=tutum/curl -it --restart=Never --rm client-pod

curl 172.17.0.8:8000
```

​	这个命令创建了一次性的pod，在退出时，pod自动销毁。

应用场景： 测试多个pod之间的连通性



#### 方法三：端口映射

在开发阶段，与pod交互最简单的方法就是端口映射。这个方法会通过代理实现网络访问。

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210301230643.png)

```
kubectl port-forward kubia 8080

# 本地运行
curl localhost:8080
```

这个方法不需要查看pod的ip，可以在本地发起请求。

应用场景：操作简单，但是背后原理复杂。如果背后出现问题，不好排查。

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210301231211.png)

curl先连接到代理，代理连接到API server，再连接到kubelet，然后连接到对应的pod。中间涉及到的环节太多。



### 5.3.1 查看日志

```bash
kubectl log kubia
# 实时日志
kubectl log kubia -f
# 显示时间戳
kubectl log kubia --timestamps=true
# 最近两分钟的日志
kubectl log kubia --since=2m
# 指定开始时间
kubectl logs kubia --since-time=2020-02-01T09:50:00Z
# 显示最近10行
kubectl logs kubia --tail=10
```

k8s为每个容器都单独保存了日志。日志通常存放在`/var/log/containers`目录。pod删除后，所有的日志也会删除。所以你需要指定一个中心化的日志系统。

k8s中，通常应用会把日志写入标准输出及标准错误。如果不这样做，而是把日志写入文件呢？

那你需要关注如何查看这些日志文件。理想情况下，你需要配置一个中心化的日志系统，但是有时候，你希望事情保持简单，而不用关系如果查看这些日志。下面的章节中，你会学习到如何将日志文件从容器中复制到你自己的电脑上。