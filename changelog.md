# AutoWater 更新日志

## v1.0.0 - 2025/11/23

正式版本。

## v1.1.0 - 2025/11/24

### Added

- 增加贴表情功能。

- 增加指定id回复功能。 by Hikari

- 增加指定关键字回复功能。

### Changed

- 重写配置逻辑，现在配置全部存储在 `config.json` ，无需手动更改代码。

- 更新了Readme。

### Fixed

- 修复缩进错误导致的无法识别群聊id。

- 修复贴表情后的意外报错退出。

## v1.1.1 - 2025/11/25

- Fixed: 紧急修复了关键词回复崩溃。

## v1.2.0 - 2025/11/25

### Added

- 增加复读功能。现在在接收到连续相同两个消息后会有概率复读（相同消息只会复读一次）。可以设置复读概率 `repeat_possibility` 。

- 增加随机回复消息功能。现在在接收到消息后可以随机用空文本回复该消息并艾特。可以设置随机回复消息概率 `at_possibility` 。

- 增加了回复的等待时间，现在对于不同的事件会执行不同的等待逻辑：

    - 复读：等待 `0.2` s。

    - 指定对象回复、关键字回复和随机输出：等待 `文本长度*1.5 + 回复长度` s，来模拟阅读和输出。

    - 贴表情和随机回复消息：等待 `3` s。
    
这样可以让回复变得更智能。

### Changed

- 为了实现复读功能重写了一点代码逻辑。

## v1.3.0 - 2025/11/28

### Added

- 增加随机戳一戳功能。可以设置随机戳一戳概率 `poke_possibility` 。戳一戳的等待时间是 `3` s。不能戳一戳的问题来源于PacketBackend不支持最新版本的QQNT，按Napcat文档配置相应的QQNT实例即可。

- 增加被艾特随机回复功能。可以设置被艾特随机回复的内容 `ated_reply` 和概率 `ated_reply_posibility` 。被艾特随机回复的等待时间是 `回复长度 + 1` s。

- 增加每天特定时间发送特定消息功能。可以设置是否启用该功能 `do_report` 。可以在 `time_reply` 里设置播报时间和内容。

### Changed

- 现在贴表情不会影响是否进行随机艾特/戳一戳/随机回复了。

- 现在如果触发了被艾特回复不会执行关键词回复、指定对象回复、贴表情、随机艾特、戳一戳、随机回复了。

- 为了实现播报功能重写了一点代码逻辑。

## v1.3.1 - 2025/11/30

- Fixed: 重写等待逻辑从而修复了收到较长文本导致 `ConnectionClosedError` 的问题。

## v1.4.0 - 2025/12/1

### Added

- 增加接入OpenAI兼容的LLM进行随机回复功能。目前仅测试了 `deepseek-chat` 。需要在 `config.json` 中配置LLM相关内容（见readme）。LLM回复的等待时间是：第一条消息为标准回复时间（见下文），此后的消息为 `回复长度*0.3` s。

- 增加了被艾特时调用LLM进行随机回复功能。可以设置被艾特并触发被艾特回复时调用LLM的概率 `ated_reply_llm_possibility` 。调用逻辑同上所述。

### Changed

- 重写等待时间：现在指定对象回复、关键字回复、LLM回复和随机输出都采用标准回复时间进行等待。标准回复时间是为了模拟人的阅读与打字速度。标准等待时间由输入和输出时间两部分组成：如果字符数小于 `30` ，则输入时间为 `0` s，否则为 `字符数*0.2` s。输出时间等于 `回复长度*0.3` s 。

- 被艾特随机回复的等待时间改为 `回复长度 * 0.3 + 1` s。

- 为实现LLM回复重写代码逻辑。

### Fixed

- 修复了原文本提取逻辑导致对于图片消息回复等待时间过长的问题。

## v1.4.1 - 2025/12/2

- Added: 增加了LLM回复分隔功能，默认分隔符是 `%n` 。可以在prompt里面让大模型用 `%n` 对句子进行分割，Autowater会分别将分割的结果输出。（by M42）

- Changed: 重写代码逻辑，拆分了文件。（by Uint）

## v1.5.0-Beta-1 - 2025/12/3

**Noted: 本版本为预览版，可能出现一些错误和未知的Bug。更新到本版本前请备份好原来的版本。**

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
    注意三种权重之和应该为1，否则可能导致一些未知的bug。

### Fixed

- 修复了 `llm_service.py` 没有 `import json` 的bug。

- 修复了其他一些已知bug。


## v1.5.0-Beta-2 - 2025/12/3

**Noted: 本版本为预览版，可能出现一些错误和未知的Bug。更新到本版本前请备份好原来的版本。**

- Changed: 架构大改，现在变成了事件驱动的面向对象模块化设计，可扩展性变强了。（by Uint）

- *但是可读性变差了。何时出开发文档 ——M42*


## v1.5.0-Beta-3 - 2025/12/4

**Noted: 本版本为预览版，可能出现一些错误和未知的Bug。更新到本版本前请备份好原来的版本。**

### Added

- 增加了对于 `notice` 类型事件的处理，包括其他用户戳一戳其他用户、对于消息贴表情的追踪。基于此实现了跟随贴表情和自动回复功能。（by Catismfans）

- 增加了自动跟贴表情功能。可以在 `config.json` 中设置是否开启跟随贴表情及其概率 `do_follow_emoji`  `follow_emoji_possibility` 。（by Catismfans）

- 增加了检测某条消息的表情数并在超过阈值时自动回复的功能。可以在 `config.json` 中设置是否开启自动回复 `do_emoji_threshold_reply` 、自动回复概率 `emoji_threshold_reply_possibility` 及详细设置回复表情、阈值、内容 `emoji_threshold_reply` 。（by Catismfans & M42）


### Changed

- 完善了新框架中 `Message` 类对于事件的处理。~~不喜欢写 `.get()` 然后疯狂爆 `KeyError` 这一块~~ （by M42）

- 由于更新到新框架的原因暂时移除了先前的等待时间功能。该部分将在 `1.5.0-Beta-4` 中发布。（by M42）

- 移除了部分由于升级到新框架所废弃的代码。（by M42）

- 略微更新了在终端显示聊天内容的机制。（by M42）

### Fixed

- 修复了一些已知的bug。

## v1.5.0-Beta-4 "AutoWater Modularization Construction" - 2025/12/7

**Noted: 本版本为预览版，可能出现一些错误和未知的Bug。更新到本版本前请备份好原来的版本。**

### Added

- 新增了 `logger` 模块，并基于此修改了原先的事件通知系统，这样可以使终端消息显示更清晰。（by M42）

- 新增了Autowater开发者指南。（by Uint）

### Changed

- 完善了新框架的事件驱动设计。现在支持广播Autowater初始化事件 `EVENT_INIT` 并在模块中自定义事件了。（by Uint）

- 完善了新框架的模块化设计。现在将原先事件的具体处理全部模块化并放到 `/module_list` 文件夹下。（by Uint）

- 更新了定时发送模块使之适应新框架。（by M42）

- 完善了Websocket连接机制，现在Websocket会尝试自动重连了。（by M42）


## v1.5.0 "AutoWater Modularization Construction" - 2025/12/7

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