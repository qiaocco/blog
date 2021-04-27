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

从图中可以看到，k8s所谓的“自动重启”，并不是真正意义上的重启，而是原来的pod退出后，再创建一个新的pod。重启后，写入容器的文件系统中的数据都会丢失。如果想要保存数据，需要创建Volume。重启期间，初始化容器（init containers)不会再次执行。

#### 重启策略

默认情况下，不管容器怎么退出，exit code是0还是非0，k8s都会重启容器。可以通过`restartPolicy`字段，配置重启的策略。

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210426104635.png)

`Always`：默认设置。不管exit code是什么，总是重启。

`OnFailure`：exit code是非0（代表失败）时重启

`Never`：即使失败的情况下也不重启



`restartPolicy`是pod级别的属性，pod下所有容器都遵循这个策略。不能给单个pod配置`restartPolicy`属性。

#### 重启的时间间隔

如果多次调用Envoy的 `/quitquitquit`接口，你会发现，重启越来越慢了。

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210426105119.png)



第一次调用，容器立马重启。下一次调用，容器会等待一定的时间才会重启。时间间隔为20, 40, 80,160s，之后会变成5分钟。这种时间间隔的机制叫做`指数级别的补偿`（exponential back-off）。最差的情况下，需要等待5min之后，才会重启。

Note

```
当容器正常运行10mins后，时间间隔会被重置为0。这个时候再调用`/quitquitquit`接口，立马就会重启。
```

查看补偿值：

```bash
kubectl get po kubia-ssl -o json | jq .status.containerStatuses
```

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210426110026.png)

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210426110226.png)



### 6.2.2 使用存活探针检查容器健康状况

前面的章节中，我们已经知道，当应用异常退出时，k8s会自动重启。但是有些情况下，应用虽然没有退出，但是也有可能处于异常状态。例如，java程序内存泄露，出现OutOfMemoryErrors错误，jvm进程没有退出，但是应用已经无法正常使用了。k8s也需要处理类似这样的情况。

应用本身，可以通过捕获异常来解决类似的问题。但是如果出现无限循环、死锁等情况，应用不好处理的情况下，需要k8s来帮助重启应用。

#### 存活探针（liveness probes）

我们可以为每个容器定义存活探针，k8s会周期性的询问探针，该容器是否正常。如果不正常，容器就会被重启掉。

类型：

`HTTP GET`探针：发送http get请求，响应状态码为2xx或3xx为正常，其他状态码或未响应为异常。

`TCP Socket`探针：建立tcp连接，建立成功为正常。

`Exex`探针：执行命令，exit code等于0为正常，非0异常。

### 6.2.3 HTTP GET探针

在下面的清单中，kubia应用设置了最简单的HTTP GET探针。请求8080端口，`/`路由，如果响应状态码在200~399，该应用就是健康状态。默认情况下，每10s发送一次请求，如果没有在1s内响应，认为请求失败。连续失败三次，该应用高就认为是不健康的，会被终止掉。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: kubia-liveness
spec:
  containers:
    - name: kubia
      image: qiaocc/kubia:1.0
      ports:
        - name: http
          containerPort: 8080
      livenessProbe:
        httpGet:
          path: /
          port: 8080
    - name: envoy
      image: luksa/kubia-ssl-proxy:1.0
      ports:
        - name: https
          containerPort: 8443
        - name: admin
          containerPort: 9901
      livenessProbe:
        httpGet:
          path: /ready
          port: admin
        initialDelaySeconds: 10
        periodSeconds: 5
        timeoutSeconds: 2
        failureThreshold: 3
```

Envoy代理提供了一个`/ready`路由，暴露其状态。我们打开Envoy管理节点，请求`ready`路由，查看状态。envoy应用的探针，还配置了其他的属性：

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210426161247.png)

`initialDelaySeconds`：容器启动后多久，到第一次检测的时间间隔

`periodSeconds`：两次检测的时间间隔

`timeoutSeconds`：超时时间

`failureThreshold`：失败极限次数。超过这个极限次数，就会认为服务不健康。



### 6.2.4 实际操作

```bash
kubectl apply -f kubia-ssl.yaml
kubectl port-forward kubia-ssl 8080 8443 9901
# 观察kubia应用
kubectl logs kubia-liveness -c kubia -f
# 观察envoy
kubectl exec kubia-liveness -c envoy -- tail -f /var/log/envoy.admin.log
```

主动将健康检查配置为失败：

打开[http://localhost:9901](http://localhost:9901/)，点击`healthcheck/fail `按钮。

```bash
kubectl get events -w
```

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210426163609.png)

达到失败极限后，容器会关闭并重启。

```bash
# 查看RESTARTS，重启次数
kubectl get po kubia-liveness
```

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210426163955.png)

State的started字段，表示新容器启动时间。

Last State表示老容器的状态。Exit Code等于0，代表容器平缓结束。如果是被kill的话，exit code=137



### 6.2.5 使用exec和tcpSocket探针

#### tcpSocket探针

配置文件：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: kubia-liveness-tcp-socket
spec:
  containers:
    - name: kubia
      image: qiaocc/kubia:1.0
      ports:
        - name: http
          containerPort: 8080
      livenessProbe:
        tcpSocket:
          port: 8080
        periodSeconds: 2
        failureThreshold: 1

```

这个探针，会检查8080端口是否能建立tcp连接。

#### exec探针

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: kubia-liveness-exec
spec:
  containers:
    - name: kubia
      image: qiaocc/kubia:1.0
      ports:
        - name: http
          containerPort: 8080
      livenessProbe:
        exec:
          command:
            - /usr/bin/healthcheck
        periodSeconds: 1
        failureThreshold: 1
```

exec探针会调用/usr/bin/healthcheck命令，检查exec code是否为0.



### 6.2.6 启动探针(startup probe)

默认的存活探针，会设置预留20~30s，让应用启动起来。如果应用启动的太慢，会导致重启。如果重启也很慢，会导致再次重启，最终变成重启地狱。

为了避免这种情况，可以把`initialDelaySeconds`, `periodSeconds` 和 `failureThreshold`设置大一点。这样设置不太好。

所以我们需要引入启动探针。启动探针只会在容器启动后执行一次，启动成功后，k8s就会使用存活探针了。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: kubia-startup-probe
spec:
  containers:
    - name: kubia
      image: luksa/kubia:1.0
      ports:
        - name: http
          containerPort: 8080
      startupProbe:
        httpGet:
          path: /
          port: http
        periodSeconds: 10
        failureThreshold: 12
      livenessProbe:
        httpGet:
          path: /
          port: http
        periodSeconds: 5
        failureThreshold: 1
    - name: envoy
      image: luksa/kubia-ssl-proxy:1.0
      ports:
        - name: https
          containerPort: 8443
        - name: admin
          containerPort: 9901
      livenessProbe:
        httpGet:
          path: /ready
          port: admin
        initialDelaySeconds: 10
        periodSeconds: 3
        timeoutSeconds: 2
        failureThreshold: 5
```

启动探针和存活探针，使用相同的路由`/`。应用启动后120s后，才会调用存活探针。启动后，每5s调用一次存活探针。

下图描述了两种探针的活动：

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210426201719.png)

### 6.2.7 创建有效的存活探针处理器

#### 存活探针导致不必要的重启

如果存活探针实现有问题，当容器正常时，探针还返回有问题，就会导致应用不必要的重启。

#### 存活探针应该检查什么

存活探针应该检查应用内部逻辑，不用检查应用依赖的组件。例如前端应用探针，不检查后端。例如，后端数据库连接不上了，即使前端探针检查失败，重启了前端，也解决不了问题。

#### 保持存活探针轻量级

存活探针，不应该需要很多系统资源，也不应该花费很长时间来执行。

#### 避免重试循环

让存活探针尽量简单，不要在探针处理器内部，写重试逻辑。使用k8s默认的重试机制就好。



## 6.3 在容器启停时执行额外的操作

前面的章节中介绍过，init容器可以在pod声明周期前，运行额外的容器。你可能想在每次运行的启停前后，执行额外的操作。你可以增加`生命周期钩子`（lifecycle hooks）。目前有两种钩子：

`post-start`钩子：容器启动前执行

`pre-stop`钩子：容器停止前执行

每个容器，可以配置自己的钩子。之前的init 容器，只能配置在pod级别。

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210427104219.png)

跟存活探针一样，lifecycle hooks也可以做：

- 在容器中执行命令
- 向容器发送http get请求

```
Note：
lifecycle hooks和存活探针一样，都只能应用到常规容器，不能应用到init容器。
lifecycle hooks还不支持tcpSocket处理器。
```

### 6.3.1 使用post-start钩子

post-start钩子在容器创建后执行，你可以使用exec执行命令，或者发送http get请求。

如果你是应用的作者，那么这些操作在应用内部就可以完成。但是如果你不能修改容器中的代码，你就可以使用post-start钩子完成类似的任务。

下面我们做一个联系，会用到`fortune`命令，这个命令作用是打印一条名言警句。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fortune-poststart
spec:
  containers:
    - name: nginx
      image: nginx:alpine
      lifecycle:
        postStart:
          exec:
            command:
              - sh
              - -c
              - "apk add fortune && fortune > /usr/share/nginx/html/quote"
      ports:
        - name: http
          containerPort: 80
```

当容器启动时，会调用postStart钩子，`fortune`会打印一句话，写入文件。nginx作为服务器，展示文件内容。

启动：

```bash
k apply -f fortune-poststart.yaml
# 端口转发。本地8080->容器80
kubectl port-forward fortune-poststart 8080:80
# 访问
curl http://localhost:8080/quote
```

#### 

