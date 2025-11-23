### **THU AutoWater Project 1.0.0**

#### 让水群变得简单



**这是什么？**

Autowater是由THU干（饭）主义协会自主研发的一款基于Napcat的全自动水群插件。

该插件目前可以做到：

· 接收到消息后0.15概率随机输出"喵",'太强了','饱饱','🈷️','和我做','强强！？','我是区','麦若，，，','妈妈','何意味','和一位','区，，，'中的一个

以后希望做到：

· 定制特定人类的回复

· 贴表情

· 复读



**部署方法**

（1）部署Napcat：参见[Napcat文档](https://napneko.github.io/guide/install)

（2）新建Napcat Websocket服务端：端口3001，消息格式Array，强制推送时间，Token留空，心跳间隔5000，Host127.0.0.1，保存

（3）编辑AutoWater.py，在TARGET_GROUP里输入你要自动水群的群号，用英文逗号隔开

（4）运行AutoWater.py即可。




