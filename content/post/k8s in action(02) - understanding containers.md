---
title: "k8s in action(02) - understanding containers"
date: 2021-01-02T13:51:15+08:00
draft: false
tags: ["k8s"]
---



## 创建docker镜像

创建`app.js`文件

```javascript
const http = require("http");
const os = require("os");

const listenPort = 8080;

console.log("Kubia server starting...");
console.log("Local hostname is " + os.hostname());
console.log("Listening on port " + listenPort);

var handler = function (request, response) {
  let clientIP = request.connection.remoteAddress;
  console.log("Received request for " + request.url + " from " + clientIP);
  response.writeHead(200);
  response.write("Hey there, this is " + os.hostname() + '. ');
  response.write("Your IP is " + clientIP + '. ');
  response.end("\n");
}

var server = http.createServer(handler)
server.listen(listenPort)
```

创建Dockerfile

```dockerfile
FROM node:12

ADD app.js /app.js
ENTRYPOINT ["node", "app.js"]
```

构建：

```bash
# 构建
docker build -t kubia:latest .
# 运行
docker run --name kubia-container -p 1234:8080 -d kubia
# 查看日志
docker logs kubia-container
# 分发
# 1. 打标签
docker tag kubia qiaocc/kubia:1.0
# 2. 推送
docker push qiaocc/kubia:1.0
# 停用
docker stop kubia-container
# 删除容器
docker rm kubia-container
# 删除镜像
docker rmi kubia:latest
```

