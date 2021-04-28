---
title: "k8s in action(07) - Mounting storage volumes into the Pod’s containers"
date: 2021-04-28T14:15:49+08:00
draft: false
tags: ["k8s"]
---

# 重点

- 容器重启后，能够持久化文件
- 在同一个pod的不同容器间共享文件
- 在不同pod间共享文件
- 挂载网络存储
- 获取host node的文件系统



# 7.1 引入Volume

一个pod就像逻辑上的一台计算机，上面运行着多个应用。应用可能包含多个进程，它们共享着CPU，内存、网络接口等。在真实的计算机上，多个进程使用的是同一个文件系统。但是在pod中不是这样的。每个容器的文件系统都是隔离的。

容器启动后，可以修改文件系统，添加文件。当容器“重启”后，这些修改不会保存，直接复原了。因为容器的”重启“，并不是真正的重启，而是杀掉老的容器，重新建一个新的容器。这时候，我们需要Volume的挂载功能。



### 7.1.1 理解volume

Volume是pod下的一个组件，volume定义在pod级别，挂载到容器指定的位置。

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210428160333.png)

volume的生命周期绑定在pod上，独立于它挂载的容器，所以volume通常用作数据持久化。

#### 在容器重启期间，持久化数据

