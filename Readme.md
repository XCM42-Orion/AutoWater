# **THU AutoWater Project 1.1.1**

## 让水群变得简单



### 这是什么？

Autowater是由THU干（饭）主义协会自主研发的一款基于Napcat的全自动水群插件。

该插件目前可以做到：

- 接收到消息后随机输出

- 定制对特定id或关键词的回复

- 贴表情

以后希望做到：

- 复读

- 更友善的config配置界面

### 部署方法

1. 部署Napcat：参见[Napcat文档](https://napneko.github.io/guide/install)

2. 新建Napcat Websocket服务端：端口3001，消息格式Array，强制推送时间，Token留空，心跳间隔5000，Host127.0.0.1，保存

3. 按照示例中的格式配置config.json:

    - target_groups(list):你要水群的群号

    - random_reply(list):随机回复的内容

    - set_reply(list):对于特定QQ的特定回复

    - set_emoji(list):对于特定QQ的贴表情,表情id参见[QQ机器人文档](https://bot.q.qq.com/wiki/develop/api-v2/openapi/emoji/model.html)

    - keyword_reply(list):对于关键字的回复

    - keyword_possibility(float):关键字回复概率

    - set_reply_possiblity(float):对于特定QQ的回复概率

    - emoji_possibility(float):贴表情的概率

    - random_reply_possibility(float):随机回复的概率

    - napcat_url(string):你的Napcat WebSocket Server地址

    - repeat_possibility(float):复读概率

4. 运行AutoWater.py即可。

### 贡献者

|  |  |
|-|-|
| M42 | 完成了大部分的代码编辑工作。|
| Hikari | 完成了特定id回复的工作。|
| Uint |  提出了很多很有益的点子~~并且写了一个接入LLM的bot然后差点把O5草了~~。|

### 最近更新

### v1.2.0 - 2025/11/25

### Added

- 增加复读功能。现在在接收到连续相同两个消息后会有概率复读（相同消息只会复读一次）。可以设置复读概率`repeat_possibility`。

- 增加随机回复消息功能。现在在接收到消息后可以随机用空文本回复该消息并艾特。可以设置随机回复消息概率`at_possibility`。

- 增加了回复的等待时间，现在对于不同的事件会执行不同的等待逻辑：

    - 复读：等待`0.2`s。

    - 特定回复、关键字回复和随机输出：等待`文本长度*1.5 + 回复长度` s，来模拟阅读和输出。

    - 贴表情和随机回复消息：等待`3`s。
    
这样可以让回复变得更智能。

### Changed

- 为了实现复读功能重写了一点代码逻辑。