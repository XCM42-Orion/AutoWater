# **THU AutoWater Project**

## 让水群变得简单



### 这是什么？

Autowater是由THU干（饭）主义协会自主研发的一款基于Napcat的全自动水群插件。

该插件目前可以做到：

- 接收到消息后随机输出

- 定制对特定id或关键词的回复

- 对特定对象贴表情

- 复读

- 随机回复消息并艾特

- 被艾特后随机回复

- 随机戳一戳

- 特定时间播报

以后希望做到：

- 更友善的config配置界面

- （待定）调用LLM进行随机回复

- 调用LLM随机回复表情


### 部署方法

1. 部署Napcat：参见[Napcat文档](https://napneko.github.io/guide/install)

2. 新建Napcat Websocket服务端：端口3001，消息格式Array，强制推送时间，Token留空，心跳间隔5000，Host127.0.0.1，保存

3. 按照示例中的格式配置config.json:

    - target_groups(list):你要水群的群号

    - random_reply(list):随机回复的内容

    - set_reply(list):对于特定对象的特定回复

    - set_emoji(list):对于特定对象的贴表情,表情id参见[QQ机器人文档](https://bot.q.qq.com/wiki/develop/api-v2/openapi/emoji/model.html)

    - keyword_reply(list):对于关键字的回复

    - ated_reply(list):被艾特后的随机回复

    - time_reply(list):特定时间的播报

    - keyword_possibility(float):关键字回复概率

    - set_reply_possiblity(float):对于特定对象的回复概率

    - emoji_possibility(float):贴表情的概率

    - random_reply_possibility(float):随机回复的概率

    - napcat_url(string):你的Napcat WebSocket Server地址

    - repeat_possibility(float):复读概率

    - at_possibility(float):随机艾特回复消息概率

    - ated_reply_possibility(float):被艾特后随机回复的概率

    - poke_possibility(float):随机戳一戳概率

    - do_report(bool):是否开启体育锻炼时间到了播报

4. 运行AutoWater.py即可。

### 贡献者

|  |  |
|-|-|
| M42 | 完成了大部分的代码编辑工作。|
| Hikari | 完成了特定id回复的工作。|
| Uint |  提出了很多很有益的点子~~并且写了一个接入LLM的bot然后差点把O5草了~~。|

### 最近更新

### v1.3.0 - 2025/11/28

### Added

- 增加随机戳一戳功能。可以设置随机戳一戳概率`poke_possibility`。戳一戳的等待时间是`3`s。不能戳一戳的问题来源于PacketBackend不支持最新版本的QQNT，按Napcat文档配置相应的QQNT实例即可。

- 增加被艾特随机回复功能。可以设置被艾特随机回复的内容`ated_reply`和概率`ated_reply_posibility`。被艾特随机回复的等待时间是`回复长度 + 1`s。

- 增加每天特定时间发送特定消息功能。可以设置是否启用该功能`do_report`。可以在`time_reply`里设置时间和内容。

### Changed

- 现在贴表情不会影响是否进行随机艾特/戳一戳/随机回复了。

- 现在如果触发了被艾特回复不会执行关键词回复、指定对象回复、贴表情、随机艾特、戳一戳、随机回复了。
