---
title: "k8s in action(06) - Managing the lifecycle of the Pod’s containers"
date: 2021-04-22T18:13:42+08:00
draft: false
tags: ["k8s"]
---

# 重点

1. 检查pod状态
2. 利用存活探针检查健康状态
3. 使用pod钩子，在启停时做额外的操作
4. 理解pod的声明周期



## 理解pod状态

创建pod之后，我们需要查看pod状态。从pod清单中，可以查看到提供了pod的状态。pod状态包含以下的信息：

- pod和node的ip地址
- pod启动时间
- pod的服务质量(QoS)
- pod的阶段
- 容器状态

### 6.1.1 理解pod阶段(phase)

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210423155401.png)

`Pending`：创建pod后，进入初始化阶段。在pod调度到node，拉取镜像并启动后，才会到下个阶段。

`Running`：至少有一个容器运行起来了

`Succeeded`：当所有容器都启动成功后，变成该状态。

`Failed`：有一个容器失败了，该pod就变成失败。

`Unknown`：kubelete没有想api server报告状态。可能因为worker node有问题，或者网络连接异常。

例子：

```bash
kubectl apply -f kubia.yaml
kubectl get po kubia -o yaml | grep phase # phase: Running
```

还可以使用`jq`工具来格式化：

```bash
kubectl get po kubia -o json | jq .status.phase
```



### 6.1.2 理解pod condition

`PodScheduled`：pod被调度到node节点

`Initialized`：初始化容器(init containers)运行成功

`ContainersReady`：所有的容器都准备好了

`Ready`：pod准备好对外提供服务了。就绪探针返回ok。

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210424103407.png)

从图中可以看出，`PodScheduled`和`Initialized`刚开始是未完成，很快就变成已完成。

`Ready`和`ContainersReady`在pod的生命周期中，可能会变换好几次状态。

之前，我们介绍过node的状态有`MemoryPressure`、`DiskPressure`、`PIDPressure` 、`Ready`。

可以看出，每种k8s对象都有自身的状态值，通常他们都会有`Ready`状态。

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210424104525.png)

如果有的阶段未完成，可以查看原因：

```bash
kubectl get po kubia -o json | jq .status.conditions
```

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210424105122.png)

`status`：是否已完成 True/False/Unknown

`reason`：未完成时，显示原因。还有`message`字段显示详情

`lastProbeTime`：上次检查时间

`lastTransitionTime`：上次状态变化的时间



### 6.1.3 容器的状态

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210424105617.png)

`Waiting`：容器将要启动。`reason`和`message`字段会显示原因

`Running`：正在运行。`startedAt`字段代表容器启动时间。

`Terminated`：进程关闭时间。`startedAt`和`finishedAt`表示启动和终止时间。`exitCode`表示主进程终止的exit code。

`Unknown`：未知。

```bash
kubectl describe po kubia
```

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210424110135.png)



## 6.2 容器的健康问题

### 6.2.1 理解容器的自动重启

pod调度到node后，kubelet会启动容器。当容器意外退出时，k8s会自动重启容器。

```bash
kubectl apply -f kubia-ssl.yaml
kubectl port-forward kubia-ssl 8080 8443 9901

# 观察
kubectl get pods -w
kubectl get events -w
```

你可以发送`KILL`信号，主动让进程退出。但是在容器中，就不能杀掉root进程（pid=1）。Envoy管理界面，提供了一个接口，可以杀掉主进程。

打开`http://localhost:9901/`页面，点击`quitquitquit`按钮，主动杀掉主进程。

再次查看状态

```
kubectl get pods -w
kubectl get events -w
```

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210425195146.png)

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210425195047.png)

pod的状态从`Running`到`NotReady` 、`CrashLoopBackOff`，最终变为`Running`。