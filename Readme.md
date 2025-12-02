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

- 被艾特后随机回复（预设回复或调用LLM）

- 随机戳一戳

- 特定时间进行播报

- 使用LLM进行随机回复

以后希望做到：

- 更友善的config配置界面

- 调用LLM随机回复表情


### 部署方法

1. 部署Napcat：参见[Napcat文档](https://napneko.github.io/guide/install)

2. 新建Napcat Websocket服务端：端口3001，消息格式Array，强制推送事件，Token留空，心跳间隔5000，Host127.0.0.1，保存

3. 按照示例中的格式配置config.json:

    - target_groups(list):你要水群的群号

    - random_reply(list):随机回复的内容

    - set_reply(list):对于特定对象的特定回复

    - set_emoji(list):对于特定对象的贴表情,表情id参见[QQ机器人文档](https://bot.q.qq.com/wiki/develop/api-v2/openapi/emoji/model.html)

    - keyword_reply(list):对于关键字的回复内容

    - ated_reply(list):被艾特后的随机回复内容

    - time_reply(list):特定时间的播报内容（时间与播报内容）

    - keyword_possibility(float):关键字回复概率

    - set_reply_possiblity(float):对于特定对象的回复概率

    - emoji_possibility(float):贴表情的概率

    - random_reply_possibility(float):随机回复的概率

    - napcat_url(string):你的Napcat WebSocket Server地址

    - repeat_possibility(float):复读概率

    - at_possibility(float):随机艾特回复消息概率

    - ated_reply_possibility(float):被艾特后随机回复的概率

    - ated_reply_llm_possibility(float):被艾特并触发被艾特回复时调用LLM的概率

    - poke_possibility(float):随机戳一戳概率

    - llm_possibility(float):调用大模型随机回复概率

    - do_report(bool):是否开启特定时间播报

    - llm_settings(dict)

        - url(string):模型提供商的URL

        - model(string):你要使用的模型

        - temperature(float):模型温度，参考API文档

        - max_tokens(int):最大token

        - background_message_number(int):一起发送给LLM帮助识别上下文的消息数

        - apikey(string):你的API Key

        - prompt(string):你使用的prompt（提示词）

4. 运行AutoWater.py即可。

### 贡献者

|  |  |
|-|-|
| M42 | 完成了大部分的代码编辑工作。|
| Hikari | 完成了特定id回复的工作。|
| Uint |  提出了很多很有益的点子，完成了代码重构的工作~~并且写了一个接入LLM的bot然后差点把O5草了~~。|

### 最近更新

### v1.4.0 - 2025/12/1

### Added

- 增加接入OpenAI兼容的LLM进行随机回复功能。目前仅测试了 `deepseek-chat` 。需要在 `config.json` 中配置LLM相关内容（见readme）。LLM回复的等待时间是：第一条消息为标准回复时间（见下文），此后的消息为 `回复长度*0.3` s。

- 增加了被艾特时调用LLM进行随机回复功能。可以设置被艾特并触发被艾特回复时调用LLM的概率 `ated_reply_llm_possibility` 。调用逻辑同上所述。

### Changed

- 重写等待时间：现在指定对象回复、关键字回复、LLM回复和随机输出都采用标准回复时间进行等待。标准回复时间是为了模拟人的阅读与打字速度。标准等待时间由输入和输出时间两部分组成：如果字符数小于 `30` ，则输入时间为 `0` s，否则为 `字符数*0.2` s。输出时间等于 `回复长度*0.3` s 。

- 被艾特随机回复的等待时间改为 `回复长度 * 0.3 + 1` s。

- 为实现LLM回复重写代码逻辑。

### Fixed

- 修复了原文本提取逻辑导致对于图片消息回复等待时间过长的问题。
