---
title: "k8s in action(02) understanding containers"
date: 2021-01-02T13:51:15+08:00
draft: false
tags: ["k8s"]
---



## 创建docker镜像

创建`app.js`[文件](https://github.com/qiaocco/kubernetes-in-action-2nd-edition/blob/master/Chapter02/kiada-0.1/app.js)

创建Dockerfile

```dockerfile
FROM node:16
COPY app.js /app.js
COPY html/ /html
ENTRYPOINT ["node", "app.js"]
```

构建：

```bash
# 构建
docker build -t kiada:latest .
# 运行
docker run --name kiada-container -p 1234:8080 -d kiada
# 查看日志
docker logs kiada-container
# 分发
# 1. 打标签
docker tag kiada qiaocc/kiada:0.1
# 2. 推送
docker push qiaocc/kiada:0.1
# 停用
docker stop kiada-container
# 删除容器
docker rm kiada-container
# 删除镜像
docker rmi kiada:latest
```

