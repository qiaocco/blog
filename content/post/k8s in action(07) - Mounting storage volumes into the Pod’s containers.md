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

在pod设置好以后，容器启动前，就会创建Volume。pod关闭时，关闭volume。当容器重启后，volume自动挂载到容器。容器可以向volume进行读写操作。

volume典型的使用场景是数据持久化。如果没有使用volume，容器重启后，无法持久化数据。

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210507103629.png)

应用的开发者要指定，哪些文件需要持久化。通常会把应用状态持久化，但是不会把缓存数据持久化。

#### 在容器中挂载多个volume

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210507103954.png)

一个pod可以有多个volume，一个容器挂载多个volume。

#### 在多个容器中共享文件

一个volume可以挂载到多个容器中，一个使用场景是，主容器和sidebar容器，需要操作同一个文件。

例如，你创建了一个pod，里面包含两个容器。web server容器作为服务器，content agent容器用来生成静态的文本内容。每个容器，承担着独立的任务，我们需要使用volume把它们结合起来。

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210507110715.png)

同一个volume，可以挂载到不同容器的不同位置上。content agent容器把文本内容写入`/var/data`，所以需要挂载这个路径。web server容器希望文件内容在`/var/html`，也需要挂载起来。

图中可以看到，volume在不同容器中，有不同的权限。在web server中，只需要读文件，所以只有read only权限。在content agent中，有read & write权限。

volume还有很多应用场景。例如 ，在sidecar容器中，需要使用工具，来处理主容器中的日志文件。在init 容器中，创建配置文件

#### 在pod重启过程中，持久化文件

volume是绑定到pod的，它的生命周期和pod一样。但是，如果我们想要pod重启后，仍然持久化保存文件，该怎么办呢?

如图，volume可以把持久化存储，映射到pod外部。这种情况下，volume的文件不是本地文件了，而是挂载到nas上，nas不再绑定到pod的生命周期上。因此，volume的内容将会被持久化下来。即使pod被删除掉，重新创建pod，volume内容依然可以挂载到新的pod上。

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210507112454.png)

#### 在不同pod之间，共享数据

如图，三个pod共享同一个volume。

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210507173657.png)

最简单的情况是，持久化volume可以是worker node的文件系统。pod位于同一个node。

当持久化volume是nas时，pod可以位于不同的node。