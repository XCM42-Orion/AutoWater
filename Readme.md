 # <center>**THU AutoWater Project**</center>

## <center>让水群变得简单</center>

<center> 

![Stars](https://img.shields.io/github/stars/XCM42-Orion/AutoWater) ![Forks](https://img.shields.io/github/forks/XCM42-Orion/AutoWater) 

</center>


### 这是什么？

Autowater是由THU干（饭）主义协会自主研发的一款基于Napcat的全自动水群插件。

该插件目前可以做到：

- 接收到消息后随机输出

- 定制对特定id或关键词的回复

- 对特定对象贴表情

- 跟贴表情

- 贴表情数量达到一定数量后自动回复

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

    - do_heartflow(dict) : 是否开启心流回复。

        - api_url(string) : 小参数模型API URL

        - api_key(string) : 小参数模型API key

        - model(string) : 小参数模型

        - background_message_number(int) : 判断是否回复时参考的消息数

        - temperature(float) : 小参数模型温度

        - willing_weight(float) : 回复意愿权重

        - context_weight(float) : 上下文参考权重

        - random_weight(float) : 随机权重（这三个权重相加应为1）

        - energy_recover_rate(float) : 精力回复速度（暂未启用）

        - reply_threshold(float) : 回复阈值，0~1之间
    
    - emoji_threshold_reply(list): 表情阈值回复配置

    - do_follow_emoji(bool): 是否跟贴表情

    - follow_emoji_possibility(float)：跟贴表情概率

    - do_emoji_threshold_reply(bool): 是否开启表情阈值回复

    - emoji_threshold_reply_possibility(float): 表情阈值回复概率 

4. 运行AutoWater.py即可。

### 贡献者

|  |  |
|-|-|
| M42 @XCM42-Orion | 完成了大部分的代码编辑工作。|
| Uint @unsigned123 | 完成了v1.5.0代码重构的工作~~并且写了一个接入LLM的bot然后差点把O5草了~~。|
| Catismfans @Just-lose-it | 完成了notice事件的处理以及关于贴表情的模块。 |
| Hikari @mickey-jj | 完成了特定id回复的工作。|

### 最近更新

### v1.5.0 "AutoWater Modularization Construction" - 2025/12/7

**Autowater重大更新：AutoWater Modularization Construction（AWMC）现已发布。**

### Feature

- **全面重写了Autowater的架构。目前的Autowater框架采用事件驱动的协程模块化面向对象设计，详情参考开发者指南。（by Uint）**

### Added

- 增加了预览版的心流（Heartflow）回复功能。可以在 `config.json` 当中配置心流相关参数 `heartflow_settings` 。可以配置如下参数：

    - `do_heartflow` : 是否开启心流回复。
    - `api_url` : 小参数模型API URL
    - `api_key` : 小参数模型API key
    - `model`: 小参数模型
    - `background_message_number`: 判断是否回复时参考的消息数
    - `temperature`: 小参数模型温度
    - `willing_weight`: 回复意愿权重
    - `context_weight`: 上下文参考权重
    - `random_weight`: 随机权重
    - `energy_recover_rate`: 精力回复速度（暂未启用）
    - `reply_threshold`: 回复阈值

    判断是否回复采用的是将小参数模型返回的回复意愿和上下文参考意愿分别乘以对应权重相加，再加上随机数乘随机权重。最后的结果如果大于回复阈值则输出回复。该机制是预览版的机制，以后会再进行更新。
    注意三种权重之和应该为1，否则可能导致一些未知的bug。（by M42）

- 增加了对于 `notice` 类型事件的处理，包括其他用户戳一戳其他用户、对于消息贴表情的追踪。基于此实现了跟随贴表情和自动回复功能。（by Catismfans）

- 增加了自动跟贴表情功能。可以在 `config.json` 中设置是否开启跟随贴表情及其概率 `do_follow_emoji`  `follow_emoji_possibility` 。（by Catismfans）

- 增加了检测某条消息的表情数并在超过阈值时自动回复的功能。可以在 `config.json` 中设置是否开启自动回复 `do_emoji_threshold_reply` 、自动回复概率 `emoji_threshold_reply_possibility` 及详细设置回复表情、阈值、内容 `emoji_threshold_reply` 。（by Catismfans & M42）

- 新增了 `logger` 模块，并基于此修改了原先的事件通知系统，这样可以使终端消息显示更清晰。（by M42）

- 新增了预览版Autowater开发者指南。（by Uint）

### Changed

- 基于新架构重写了原有的模块。（by M42 & Uint）

- 基于新增的 `logger` 模块重写了原有模块的终端事件推送模式。（by M42）

- 重写了原有的等待系统，现在的等待系统以 `delay` 模块的形式加入。新的等待系统结构如下：（by M42）

|返回算法|介绍|使用该算法的模块|
|-|-|-|
| `standard_delay` |标准回复时间。标准回复时间是为了模拟人的阅读与打字速度。标准等待时间由输入和输出时间两部分组成：如果输入字符数小于 `10` ，则输入时间为 `0` s，否则为 `输入字符数*0.2` s。输出时间等于 `输出字符数*0.3` s 。|随机回复、LLM回复、被艾特LLM回复、关键词回复、贴表情阈值回复|
| `only_output_delay` |仅输出延迟时间。等待时间为 `输出字符数*0.3 + 1` s。|被艾特预定义回复、特殊用户回复|
| `only_input_delay` |仅输入延迟时间。如果输入字符数小于 `10` ，则等待时间为 `0` s，否则等待时间为 `输入字符数*0.2` s。|暂未使用|
| `constant_delay` |等待固定时间，例如固定等待 `0.2` s。|戳一戳、随机艾特、贴表情、跟贴表情|

- 完善了Websocket连接机制，现在Websocket会尝试自动重连了。（by M42）

- 移除了部分由于升级到新框架所废弃的代码。（by M42）

### Fixed

- 修复一些已知的bug。
