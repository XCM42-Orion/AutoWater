# Autowater 配置指南

本文档旨在让你从零开始部署Autowater。

## 安装 Autowater

1. 安装最新版本的 Python：[Python Downloads](https://www.python.org/downloads/)

2. 安装 pip：[pip Documents](https://pip.pypa.io/en/stable/installation/)

3. 从Github下载最新版本的 Autowater Release：[Autowater Releases](https://github.com/XCM42-Orion/AutoWater/releases)

    下载后，将 Autowater 解压到你喜欢的位置。

    也可以使用 Git Clone：

    ``` powershell
    git clone git@github.com:XCM42-Orion/AutoWater.git
    ```

    安装成功后，使用 pip 安装 Autowater 的依赖。

    ``` powershell
    cd AutoWater
    pip install -r requirements.txt
    ```

4. 安装 Napcat ：[Napcat Document](https://napneko.github.io/guide/napcat)

## 配置 Napcat WebSocket 服务端

根据 Napcat 文档，登录后在 Napcat WebUI 新建 WebSocket 服务器：

- `token` 留空

- 消息格式：`Array`

- 关闭上报自身消息

如果不懂其他配置，留空即可。配置完成后启用服务器。**注意：由于没有设置token，请不要把 Napcat 的端口暴露到公网。**

## 配置 Autowater 配置项

Autowater 提供了丰富的配置项。你可以使用 Web UI 配置 Autowater 的各个配置项，也可以在 `config.json` 手动配置。目前 Web UI 还不完善，因此我们推荐使用后者。

默认的 `config.json` 提供了一个可以运行的最小实例。根据你的需求配置各个字段。

### 系统配置

| 字段名 | 类型 | 描述 | 
|-|-|-|
| `target_groups` | `list` | 启用 Autowater 回复的群号，每个群号是一个整数。可以配置多个群号。
| `napcat_url` | `string` | Napcat 服务器的 url 。|

### 消息处理配置

| 字段名 | 类型 | 描述 | 
|-|-|-|
| `random_reply_possibility` | `float` | 随机回复的概率。|
| `random_reply` | `list` | 随机回复的内容。 |
| `set_reply_possibility` | `float` | 对特定用户执行特定回复的概率。 |
| `set_reply` | `list` | 对特定用户执行的特定回复。每一个元素是一个字典，包括 `id` （特定用户的QQ号）和 `reply` （对特定用户的回复）两个字段。|
| `emoji_possibility` | `float` | 给特定用户贴表情的概率。 |
| `set_emoji` | `list` | 给特定用户贴的表情。每一个元素是一个字典，包括 `id` （特定用户的QQ号）和 `emoji_id` （要贴的emoji的id）。|
| `do_emoji_threshold_reply` | `bool` | 是否开启贴表情阈值回复。|
| `emoji_threshold_reply_possibility` | `float` | 贴表情数量到达阈值时回复的概率。|
| `emoji_threshold_reply` | `list` | 贴表情阈值回复配置。每个元素是一个字典，包括 `emoji_id` （监控的表情id）、 `count` （贴表情阈值）和 `reply` （达到阈值时的回复列表）三个字段。|
| `do_follow_emoji` | `bool` | 是否开启跟贴表情。|
| `follow_emoji_possibility` | `float` | 跟贴表情的概率。|
| `keyword_possibility` | `float` | 关键字回复的概率。 |
| `keyword_reply` | `list` | 对特定关键字的回复。每个元素是一个字典，包括 `keyword` （要回复的关键字）和 `reply` （对特定关键字的回复列表）两个参数。|
| `repeat_possibility` | `float` | 复读概率。 |
| `at_possibility` | `float` | 随机回复并 At 其他人的概率。 |
| `ated_reply_possibility` | `float` | 被 At 时随机回复的概率。|
| `ated_reply` | `list` | 被 At 时的随机回复内容池。|
| `ated_reply_llm_possibility` | `float` | 被 At 时调用LLM回复的概率。|
| `llm_possibility` | `float` | 收到消息时调用LLM回复的概率。|
|`palindrome_reply_possibility`|`float` | 回文回复的概率。|
|`palindrome_left_possibility`|`float`| 回文回复对称左半边的概率，从0到1的浮点数。对称右半边的概率是1 - 对称左半边的概率。
|`palindrome_headers`|`list`| 回文回复左半边添加的内容（右半边添加的内容为该内容的对称）。|
| `poke_possibility` | `float` | 收到消息后随机戳一戳的概率。|

### 定时回复配置

| 字段名 | 类型 | 描述 | 
|-|-|-|
| `do_report` | `bool` | 是否启用定时回复。|
| `time_reply` | `list` | 定时回复配置项。每一个元素是一个字典，包括 `time` （定时回复时间）和 `reply` （定时回复内容）两个配置项。|

### LLM 配置

本部分配置位于 `llm_settings` 字段下。Autowater 采用 OpenAI 兼容的 API 格式，因此请确保使用的是 OpenAI 兼容的 API。

| 字段名 | 类型 | 描述 | 
|-|-|-|
| `url` | `string` | 调用LLM的 API 接口。请直接配置到 API 的 `/chat/completions ` 接口，例如 `"https://api.deepseek.com/v1/chat/completions"`。|
| `model` | `string` | LLM 模型 id。|
| `temperature` | `float` | 模型温度。|
| `max_tokens` | `int` | 模型可使用的最大 token 数。|
| `background_message_number` | `int` | 用于构建模型上下文的消息数。|
| `apikey` | `string` | 调用模型所使用的 API Key。|
| `prompt` | `string` | 模型提示词。 |
| `multimodel` | `bool` | 模型是否支持图像模态。 |
| `thinking` | `bool` | 是否开启思考。|

### Heartflow 心流回复配置

本部分配置位于 `heartflow_settings` 字段下。Autowater 采用 OpenAI 兼容的 API 格式，因此请确保使用的是 OpenAI 兼容的 API。
注意心流回复所采用的大模型是在 `llm_settings` 字段配置的大模型。这里的模型配置是用于判断的小模型的配置。

| 字段名 | 类型 | 描述 | 
|-|-|-|
| `do_heartflow` | `bool` | 是否开启心流回复。心流回复与大模型随机回复互不干扰，故建议两个只开启一个即可。|
| `api_url` | `string` | 调用LLM的 API 接口。请直接配置到 API 的 `/chat/completions ` 接口，例如 `"https://api.deepseek.com/v1/chat/completions"`。|
| `api_key` | `string` | 调用模型所使用的 API Key。|
| `model` | `string` | 用于心流判断的小模型 id 。|
| `background_message_number` | `int` | 用于构建模型上下文的消息数。消息数将会一并用于心流判断和大模型回复。|
| `temperature` | `float` | 模型温度。|
|`willing_weight`| `float` | 回复意愿权重。用于判断模型的回复意愿在总参考当中的权重占比。|
| `context_weight` | `float` | 上下文参考权重。用于判断群聊上下文与用户的相关性在总参考当中的权重占比。|
| `random_weight` | `float` | 随机权重。用于判断随机数在总参考当中的占比。|
| `energy_recover_rate` | `float` | 精力回复速度（暂未启用）。|
| `reply_threshold`| `float` | 回复阈值。将回复意愿、上下文参考、随机数各乘以各自的权重得到的值若大于回复阈值则触发心流回复。|

### 图像转述模型配置

本部分配置位于 `vllm_settings` 字段下。Autowater 采用 OpenAI 兼容的 API 格式，因此请确保使用的是 OpenAI 兼容的 API。

| 字段名 | 类型 | 描述 | 
|-|-|-|
| `enable` | `bool` | 是否启用图像转述，|
| `url` | `string` | 调用LLM的 API 接口。请直接配置到 API 的 `/chat/completions ` 接口，例如 `"https://api.deepseek.com/v1/chat/completions"`。|
| `model` | `string` | 用于图像转述的视觉模型 id 。|
| `temperature` | `float` | 模型温度。|
| `max_tokens` | `int` | 模型可使用的最大 token 数。|
| `background_message_number` | `int` | 用于构建模型上下文的消息数。|
| `apikey` | `string` | 调用模型所使用的 API Key。|
| `prompt` | `string` | 图像转述模型提示词。 |
| `multimodel` | `bool` | 模型是否支持图像模态。 |
| `thinking` | `bool` | 是否开启思考。|

## 启动 Autowater

保存 `config,json` 文件。确认 Napcat 正常运行并启动 WebSocket 服务器后，在终端运行 `autowater.py` 。
```powershell
python autowater.py
```
如果一切顺利，Autowater会在控制台中输出消息：

```powershell
[DEBUG] Autowater启动成功。
```
接下来，Autowater 会从 Napcat 获取消息并开始运行。祝一切顺利！