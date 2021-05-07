---
title: "TCP的三次握手"
date: 2021-04-28T18:11:49+08:00
draft: false
---





# TCP三次握手的过程

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210428181424.png)

​	假设 A 为客户端，B 为服务器端。

- 首先 B 处于 LISTEN（监听）状态，等待客户的连接请求。
- A 向 B 发送连接请求报文，SYN=1，ACK=0，选择一个初始的序号 x。
- B 收到连接请求报文，如果同意建立连接，则向 A 发送连接确认报文，SYN=1，ACK=1，确认号为 x+1，同时也选择一个初始的序号 y。
- A 收到 B 的连接确认报文后，还要向 B 发出确认，确认号为 y+1，序号为 x+1。
- B 收到 A 的确认后，连接建立。



# 使用wireshark抓包，观察TCP三次握手

Step1：启动wireshark抓包。访问我自己的服务：

```bash
curl https://msg.qiaocci.com?msg=123
```

Step2：输入过滤条件获取待分析数据包列表 `ip.addr == 122.51.107.111`

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210428182306.png)

 图中可以看到wireshark截获到了三次握手的三个数据包。第四个包才是HTTP的， 这说明HTTP的确是使用TCP建立连接的。



**第一次握手数据包**

客户端发送一个TCP，标志位为SYN，序列号为0， 代表客户端请求建立连接。 如下图。

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210428185439.png)

数据包的关键属性如下：

 SYN ：标志位，表示请求建立连接

 Seq = 0 ：初始建立连接值为0，数据包的相对序列号从0开始，表示当前还没有发送数据

 Ack =0：初始建立连接值为0，已经收到包的数量，表示当前没有接收到数据

**第二次握手的数据包**

服务器发回确认包, 标志位为 SYN,ACK. 将确认序号(Acknowledgement Number)设置为客户的I S N加1以.即0+1=1, 如下图

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210428192755.png)

 数据包的关键属性如下：

[SYN+ACK]： 标志位，同意建立连接，并回送SYN+ACK

 Seq = 0 ：初始建立值为0，表示当前还没有发送数据

 Ack = 1：表示当前端成功接收的数据位数，虽然客户端没有发送任何有效数据，确认号还是被加1，因为包含SYN或FIN标志位。（并不会对有效数据的计数产生影响，因为含有SYN或FIN标志位的包并不携带有效数据）

**第三次握手的数据包**

 客户端再次发送确认包(ACK) SYN标志位为0,ACK标志位为1.并且把服务器发来ACK的序号字段+1,放在确定字段中发送给对方.并且在数据段放写ISN的+1, 如下图:

![](https://cdn.jsdelivr.net/gh/qiaocci/img-repo@master/20210428193013.png)

数据包的关键属性如下：

 ACK ：标志位，表示已经收到记录

 Seq = 1 ：表示当前已经发送1个数据

 Ack = 1 : 表示当前端成功接收的数据位数，虽然服务端没有发送任何有效数据，确认号还是被加1，因为包含SYN或FIN标志位（并不会对有效数据的计数产生影响，因为含有SYN或FIN标志位的包并不携带有效数据)。

 就这样通过了TCP三次握手，建立了连接。开始进行数据交互



# wireshark过滤器

1. 过滤IP：`ip.addr == 122.51.107.111`

2. 过滤域名：

   ```
   # 完全匹配
   http.host == msg.qiaocci.com
   # 包含关系
   http.host contains qiaocc
   # 包含关系
   http contains qiaocc
   ```



注意：过滤器不需要加引号



# 为什么要三次握手

https://www.jianshu.com/p/e7f45779008a
