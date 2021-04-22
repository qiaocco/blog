---
title: "k8s in action(06) - Managing the lifecycle of the Pod’s containers"
date: 2021-04-22T23:11:31+08:00
draft: false
tags: ["k8s"]
---



# 重点

1. 检查pod状态
2. 利用存活探针检查健康状态
3. 使用pod钩子，在启停时做额外的操作
4. 理解pod的声明周期



## 理解pod状态