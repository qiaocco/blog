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

### 6.1.1 理解pod阶段

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

