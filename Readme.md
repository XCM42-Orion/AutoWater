# **THU AutoWater Project 1.1.0**

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

4. 运行AutoWater.py即可。

### 贡献者

|  |  |
|-|-|
| M42 | 完成了大部分的代码编辑工作。|
| Hikari | 完成了特定id回复的工作。|
| Uint |  提出了很多很有益的点子~~并且写了一个接入LLM的bot然后差点把O5草了~~。|

### 最近更新

### v1.1.0 - 2025/11/24

### Added

- 增加贴表情功能。

- 增加指定id回复功能。 by Hikari

- 增加指定关键字回复功能。

### Changed

- 重写配置逻辑，现在配置全部存储在config.json，无需手动更改代码。

- 更新了Readme。

### Fixed

- 修复缩进错误导致的无法识别群聊id。

- 修复贴表情后的意外报错退出。