---
title: "k8s备忘单"
date: 2021-04-08T13:51:15+08:00
draft: false
tags: ["k8s"]
---



## 查看配置

```bash
kubectl config view # 查看配置信息
```



## 命名空间

```bash
kubectl config set-context --current --namespace=<命名空间>
# 验证之
kubectl config view | grep namespace
```

