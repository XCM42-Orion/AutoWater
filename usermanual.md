# AutoWater 开发者文档

## 第一部分：架构概述与设计理念

### 1.1 整体架构

AutoWater 是一个基于事件驱动、模块化设计的QQ机器人框架，采用现代化的异步编程模型构建。整个系统的架构可以分为以下几个核心层次：

```
┌─────────────────────────────────────────────────────┐
│                   应用层 (Application)                │
│  ┌───────────────────────────────────────────────┐  │
│  │              功能模块 (Modules)                │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐        │  │
│  │  │   LLM   │ │ HeartFlow│ │ 其他模块 │ ...   │  │
│  │  └─────────┘ └─────────┘ └─────────┘        │  │
│  └───────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────┤
│                核心框架层 (Core Framework)            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │
│  │ 事件分发系统 │ │ 模块管理系统 │ │ 消息处理系统 │  │
│  └─────────────┘ └─────────────┘ └─────────────┘  │
├─────────────────────────────────────────────────────┤
│                 通信层 (Communication)                │
│  ┌───────────────────────────────────────────────┐  │
│  │              WebSocket 客户端                  │  │
│  │      (通过Napcat连接QQ消息服务器)                │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

#### 主要组件说明：

1. **WebSocket 客户端** (`websocket_client.py`)
   - 负责与Napcat服务器建立连接
   - 接收和发送原始JSON格式的QQ消息
   - 处理网络连接和重连逻辑

2. **消息处理系统** (`message_utils.py`)
   - 提供`Message`和`MessageComponent`类，封装QQ消息的复杂结构
   - 将原始消息数据转换为易于操作的对象模型
   - 支持文本、@、图片、回复等多种消息组件

3. **事件分发系统** (`event.py`)
   - 定义事件类型和事件上下文
   - 提供优先级支持的事件监听器注册机制
   - 实现异步事件分发和处理

4. **模块管理系统** (`module.py`)
   - 提供模块基类和模块生命周期管理
   - 支持模块依赖关系解析和拓扑排序加载
   - 实现模块的动态加载和卸载

5. **配置管理系统** (`config.py`)
   - 统一管理所有配置项
   - 提供类型安全的配置访问接口
   - 支持JSON格式的配置文件

### 1.2 设计理念

#### 1.2.1 事件驱动架构

AutoWater 采用**事件驱动架构**，所有功能都围绕事件展开：

```python
# 示例：事件处理流程
1. WebSocket接收消息 → 2. 转换为Message对象 → 3. 创建Event对象
4. 分发到注册的监听器 → 5. 各模块处理事件 → 6. 生成响应
```

**核心思想**：
- **松耦合**：模块之间不直接调用，而是通过事件通信
- **可扩展性**：新功能只需注册新的事件监听器
- **异步处理**：充分利用Python的asyncio，支持并发处理

#### 1.2.2 模块化设计

系统采用**插件式架构**，所有功能都以模块形式实现：

```python
# 示例：模块结构
class MyModule(Module):
    def register(self, message_handler, event_handler, module_handler):
        # 注册事件监听器
        message_handler.register_listener(
            self, EventType.EVENT_RECV_MSG, self.on_message
        )
    
    async def on_message(self, event, context):
        # 处理消息事件
        pass
```

**设计特点**：
- **声明式依赖**：模块通过`prerequisite`声明依赖关系
- **自动拓扑排序**：系统自动解析依赖关系并按正确顺序加载
- **生命周期管理**：提供`register`/`unregister`生命周期钩子

#### 1.2.3 面向消息的对象模型

设计了丰富的消息对象模型，简化复杂消息的处理：

```python
# 示例：消息对象的创建和使用
# 创建复杂消息
msg = Message([
    ("reply", 123456),      # 回复某条消息
    ("at", 987654321),      # @某人
    "这是一条文本消息"       # 文本内容
])

# 解析收到的消息
for component in message.get_components():
    if component.type == 'at':
        print(f"被@{component.data}提到了")
```

### 1.3 设计优势

#### 1.3.1 高可扩展性

**优势体现**：
- **热插拔模块**：可以在运行时动态加载和卸载模块
- **零侵入扩展**：添加新功能无需修改现有代码
- **标准化接口**：所有模块遵循统一的接口规范

```python
# 示例：轻松扩展新功能
# 1. 创建新模块类
class NewFeature(Module):
    async def on_message(self, event, context):
        # 实现新功能逻辑
        pass
    
    def register(self, ...):
        # 注册事件监听器
        pass

# 2. 放入module_list目录即可自动加载
```

#### 1.3.2 灵活的配置管理

**优势体现**：
- **集中式配置**：所有配置项统一管理
- **类型安全**：通过Config类提供类型安全的访问
- **运行时可调整**：部分配置支持运行时调整

#### 1.3.3 强大的事件系统

**优势体现**：
- **优先级支持**：事件监听器可以设置优先级，确保处理顺序
- **异步处理**：支持协程和同步函数的事件处理
- **上下文传递**：通过EventContext在不同模块间共享状态

```python
# 示例：优先级事件处理
# 高优先级模块先处理
message_handler.register_listener(module1, EventType.EVENT_RECV_MSG, callback1, priority=0)
# 低优先级模块后处理
message_handler.register_listener(module2, EventType.EVENT_RECV_MSG, callback2, priority=10)
```

#### 1.3.4 良好的错误处理

**优势体现**：
- **异常隔离**：一个模块的异常不会影响其他模块
- **优雅降级**：关键功能失败时系统仍可运行
- **详细日志**：提供详细的调试信息

#### 1.3.5 现代化异步架构

**优势体现**：
- **全异步IO**：充分利用现代Python的异步特性
- **并发处理**：支持同时处理多个消息
- **资源高效**：避免线程阻塞，减少资源消耗

### 1.4 技术栈

- **核心语言**：Python 3.7+
- **异步框架**：asyncio
- **网络通信**：websockets
- **配置管理**：JSON
- **HTTP客户端**：aiohttp (用于API调用)
- **架构模式**：事件驱动、模块化、插件式

### 1.5 适用场景

AutoWater框架特别适用于：

1. **复杂机器人逻辑**：需要处理多种消息类型和复杂交互
2. **多模块协作**：多个功能需要协同工作的场景
3. **动态功能扩展**：需要频繁添加或修改功能的场景
4. **高可维护性需求**：需要清晰架构便于团队协作的项目

这种架构设计使得AutoWater不仅是一个QQ机器人，更是一个可扩展的机器人开发框架，为开发者提供了强大的基础能力和灵活的扩展机制。

---

*下一部分将详细介绍事件系统的设计细节和使用方法。*


# AutoWater 开发者文档

## 第二部分：事件系统设计细节与使用方法

### 2.1 事件系统架构概述

AutoWater的事件系统是整个框架的核心，它实现了**发布-订阅模式**，支持**优先级调度**和**异步处理**。事件系统的设计目标是：

1. **解耦模块**：模块之间不直接调用，通过事件通信
2. **灵活扩展**：可以轻松添加新的事件类型和处理逻辑
3. **有序执行**：通过优先级控制事件处理顺序
4. **状态共享**：通过上下文在模块间共享状态

### 2.2 核心组件详解

#### 2.2.1 EventType 枚举

`EventType` 定义了系统中所有可能的事件类型：

```python
class EventType(Enum):
    EVENT_INIT = 0          # 系统初始化事件
    EVENT_RECV_MSG = 1      # 接收消息事件（群聊消息）
    EVENT_PRE_SEND_MSG = 2  # 发送消息前事件（可修改或拦截）
    EVENT_NOTICE_MSG = 3    # 通知事件（戳一戳、表情贴等）
```

**扩展新事件类型**：
```python
# 在event.py中添加
class EventType(Enum):
    # ... 现有事件
    EVENT_USER_LOGIN = 4    # 用户登录事件
    EVENT_GROUP_CHANGE = 5  # 群信息变更事件
```

#### 2.2.2 Event 类

`Event` 类封装了一个事件的所有信息：

```python
class Event:
    def __init__(self, event_type: EventType, context: EventContext, data: Any):
        self.event_type = event_type    # 事件类型
        self.status = 0                 # 事件状态
        self.blocked = False            # 是否被阻塞
        self.data = data                # 事件数据（如Message对象）
        self.context = context          # 事件上下文
        self.history = []               # 处理历史记录
        self.status = 1                 # 初始化完成
```

**关键方法**：
```python
# 阻塞事件传播
event.block_event()  # 调用后后续监听器不会执行
```

**使用示例**：
```python
async def my_handler(event, context):
    # 检查事件类型
    if event.event_type == EventType.EVENT_RECV_MSG:
        message = event.data  # 获取消息数据
        # 处理逻辑...
        
    # 如果需要阻止其他模块处理该事件
    if some_condition:
        event.block_event()
```

#### 2.2.3 EventContext 类

`EventContext` 提供了事件处理过程中的上下文信息：

```python
class EventContext:
    def __init__(self):
        self.message_handler = None  # MessageHandler实例
        self.event_handler = None    # EventHandler实例
        self.mod = None              # ModuleHandler实例
        self.utilities = None        # 工具函数（预留）
        self.log = None              # 日志记录器（预留）
```

**访问其他模块**：
```python
async def my_handler(event, context):
    # 访问配置模块
    config = context.mod.config
    
    # 访问LLM模块
    llm_service = context.mod.llm
    
    # 发送消息
    await context.message_handler.send_message("Hello")
```

#### 2.2.4 EventHandler 类

`EventHandler` 是事件系统的核心调度器：

```python
class EventHandler:
    def __init__(self):
        # 事件类型 -> 优先级 -> 监听器列表
        self.listeners: Dict[EventType, Dict[int, List[Callable]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self.tasks: List[asyncio.Task] = []  # 任务记录
```

**数据结构说明**：
```
EventType.EVENT_RECV_MSG
├── 优先级 0
│   ├── 监听器1 (module1.on_message)
│   └── 监听器2 (module2.on_message)
├── 优先级 1
│   └── 监听器3 (module3.on_message)
└── 优先级 10
    └── 监听器4 (module4.on_message)
```

### 2.3 事件分发流程

#### 2.3.1 完整流程图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  接收原始消息     │    │  创建Event对象   │    │  分发事件       │
│  (WebSocket)    │───▶│  (process_message)│───▶│  (dispatch_event)│
└─────────────────┘    └─────────────────┘    └─────────┬───────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  处理完成       │◀───│  执行监听器      │◀───│  按优先级排序    │
│                 │    │  (同一优先级并行) │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### 2.3.2 分发算法伪代码

```python
async def dispatch_event(self, event: Event):
    # 1. 检查是否有监听器注册
    if event_type not in self.listeners:
        return
    
    # 2. 获取该事件的所有监听器
    corresponding_listeners = self.listeners[event_type]
    
    # 3. 按优先级排序（从小到大）
    sorted_priorities = sorted(corresponding_listeners.keys())
    
    # 4. 按优先级依次执行
    for priority in sorted_priorities:
        listeners = corresponding_listeners[priority]
        
        # 5. 为同一优先级的监听器创建任务
        tasks = []
        for listener in listeners:
            # 记录处理历史
            event.history.append((priority, listener.module))
            
            # 创建异步任务
            task = asyncio.create_task(listener(event, event.context))
            tasks.append(task)
        
        # 6. 等待同一优先级所有任务完成
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 7. 处理异常
            for result in results:
                if isinstance(result, Exception):
                    print(f"Listener failed: {result}")
        
        # 8. 检查事件是否被阻塞
        if event.blocked:
            return  # 停止事件传播
```

### 2.4 注册和使用监听器

#### 2.4.1 基础注册方法

```python
# 在模块的register方法中注册
class MyModule(Module):
    def register(self, message_handler, event_handler, module_handler):
        # 注册事件监听器
        message_handler.register_listener(
            self,                    # 模块实例
            EventType.EVENT_RECV_MSG, # 事件类型
            self.on_message,         # 回调函数
            priority=5               # 优先级（默认0）
        )
    
    async def on_message(self, event, context):
        """处理消息事件"""
        message = event.data
        # 业务逻辑...
```

#### 2.4.2 监听器函数签名

监听器函数必须遵循以下签名之一：

```python
# 异步函数（推荐）
async def on_event(event: Event, context: EventContext) -> None:
    pass

# 同步函数（会被自动转换为异步）
def on_event(event: Event, context: EventContext) -> None:
    pass
```

#### 2.4.3 优先级策略

**优先级规则**：
- 数值越小，优先级越高（0最高）
- 同一优先级的监听器**并行执行**
- 不同优先级的监听器**顺序执行**

**常用优先级建议**：
```python
PRIORITY_CRITICAL = 0      # 关键处理（如命令解析）
PRIORITY_HIGH = 1          # 重要处理（如权限检查）
PRIORITY_NORMAL = 5        # 普通处理（默认）
PRIORITY_LOW = 10          # 低优先级处理（如日志记录）
PRIORITY_MONITOR = 100     # 监控类处理
```

### 2.5 实践示例

#### 2.5.1 消息处理模块示例

```python
from module import Module
from event import EventType

class MessageLogger(Module):
    """消息日志记录模块"""
    
    def register(self, message_handler, event_handler, module_handler):
        # 低优先级，最后执行
        message_handler.register_listener(
            self, EventType.EVENT_RECV_MSG, 
            self.log_message, priority=100
        )
    
    async def log_message(self, event, context):
        """记录所有消息"""
        message = event.data
        print(f"[LOG] {message.nickname}({message.user_id}): {message}")
        # 不阻塞事件，让其他模块继续处理
```

#### 2.5.2 消息拦截模块示例

```python
class MessageFilter(Module):
    """消息过滤模块"""
    
    def register(self, message_handler, event_handler, module_handler):
        # 高优先级，最先执行
        message_handler.register_listener(
            self, EventType.EVENT_RECV_MSG,
            self.filter_message, priority=0
        )
    
    async def filter_message(self, event, context):
        """过滤敏感消息"""
        message = event.data
        content = str(message)
        
        # 检查敏感词
        if self.contains_sensitive_word(content):
            print(f"[FILTER] 过滤敏感消息: {content[:50]}...")
            event.block_event()  # 阻止后续处理
            return
        
        # 检查黑名单用户
        if message.user_id in self.blacklist:
            print(f"[FILTER] 拦截黑名单用户: {message.user_id}")
            event.block_event()
    
    def contains_sensitive_word(self, text):
        # 敏感词检查逻辑
        sensitive_words = ["敏感词1", "敏感词2"]
        return any(word in text for word in sensitive_words)
```

#### 2.5.3 消息修改模块示例

```python
class MessageModifier(Module):
    """消息修改模块"""
    
    def register(self, message_handler, event_handler, module_handler):
        # 中等优先级，可以修改消息内容
        message_handler.register_listener(
            self, EventType.EVENT_RECV_MSG,
            self.modify_message, priority=2
        )
    
    async def modify_message(self, event, context):
        """修改消息内容"""
        message = event.data
        
        # 创建新的消息组件
        new_components = []
        for component in message.get_components():
            if component.type == 'text':
                # 替换文本中的特定内容
                new_text = component.data.replace("旧词", "新词")
                new_components.append(MessageComponent('text', new_text))
            else:
                new_components.append(component)
        
        # 创建新消息（注意：这需要Message类支持修改）
        # 实际实现中可能需要更复杂的方式
```

### 2.6 高级特性

#### 2.6.1 事件历史追踪

每个Event对象都会记录处理历史：

```python
async def debug_handler(event, context):
    """调试处理器，查看事件处理历史"""
    print(f"事件类型: {event.event_type}")
    print("处理历史:")
    for priority, module_name in event.history:
        print(f"  - 优先级{priority}: {module_name}")
    
    # 检查是否被阻塞
    if event.blocked:
        print("事件已被阻塞")
```

#### 2.6.2 跨模块协作

通过EventContext实现模块间协作：

```python
class StatisticsModule(Module):
    """统计模块"""
    
    def __init__(self):
        self.message_count = 0
    
    async def count_message(self, event, context):
        self.message_count += 1

class ReportModule(Module):
    """报告模块，依赖统计模块"""
    
    prerequisite = ['StatisticsModule']
    
    async def periodic_report(self, event, context):
        """定时报告"""
        stats = context.mod.StatisticsModule
        print(f"已处理消息数: {stats.message_count}")
```

#### 2.6.3 自定义事件

创建和分发自定义事件：

```python
# 1. 定义新事件类型
class CustomEventType(Enum):
    EVENT_USER_ACTION = 100  # 从100开始，避免冲突

# 2. 在模块中分发自定义事件
class UserActionModule(Module):
    async def handle_user_action(self, user_id, action):
        # 创建事件上下文
        context = EventContext()
        context.message_handler = self.message_handler
        context.mod = self.module_handler
        
        # 创建事件
        event = Event(
            CustomEventType.EVENT_USER_ACTION,
            context,
            {"user_id": user_id, "action": action}
        )
        
        # 分发事件（需要访问EventHandler）
        await self.event_handler.dispatch_event(event)
```

### 2.7 调试和问题排查

#### 2.7.1 常见问题

1. **事件未触发**
   - 检查事件类型是否正确
   - 检查监听器是否注册成功
   - 检查优先级是否合适

2. **事件被意外阻塞**
   - 查看`event.history`确定哪个模块阻塞了事件
   - 检查条件判断逻辑

3. **性能问题**
   - 避免在监听器中执行耗时操作
   - 考虑使用`asyncio.sleep(0)`释放控制权

#### 2.7.2 调试工具

```python
class EventDebugger(Module):
    """事件调试器"""
    
    def register(self, message_handler, event_handler, module_handler):
        # 注册到所有事件类型
        for event_type in EventType:
            message_handler.register_listener(
                self, event_type, 
                self.debug_event, priority=999  # 最低优先级
            )
    
    async def debug_event(self, event, context):
        """调试所有事件"""
        print(f"\n=== 事件调试 ===")
        print(f"事件类型: {event.event_type}")
        print(f"事件数据: {type(event.data)}")
        print(f"处理历史: {event.history}")
        print(f"是否阻塞: {event.blocked}")
        print("===============\n")
```

### 2.8 最佳实践

1. **单一职责**：每个监听器只做一件事
2. **合理使用优先级**：避免滥用高优先级
3. **异步友好**：尽量使用异步函数，避免阻塞
4. **错误处理**：监听器内部处理好异常
5. **性能考虑**：避免在监听器中做耗时IO操作
6. **可测试性**：设计可独立测试的监听器

### 2.9 总结

AutoWater的事件系统提供了强大而灵活的事件处理机制：

- **清晰的层次结构**：EventType → Event → Listener → Handler
- **灵活的优先级控制**：支持精细的执行顺序控制
- **完善的上下文传递**：方便模块间协作
- **健壮的错误处理**：异常不会影响其他监听器
- **良好的扩展性**：轻松添加新事件类型和监听器

通过合理使用事件系统，可以构建出高度模块化、可维护的机器人应用。

---

*下一部分将详细介绍模块系统的设计和使用方法。*
# AutoWater 开发者文档

## 第三部分：模块系统的设计和使用方法

### 3.1 模块系统概述

AutoWater 的模块系统采用**插件化架构**，支持**动态加载、依赖管理、生命周期控制**。模块系统的设计目标是：

1. **高内聚低耦合**：每个模块功能独立，通过事件系统通信
2. **动态热插拔**：支持运行时加载和卸载模块
3. **依赖管理**：自动解析模块依赖关系，按正确顺序加载
4. **统一接口**：所有模块遵循相同的接口规范

### 3.2 核心组件详解

#### 3.2.1 Module 基类

所有模块必须继承自 `Module` 基类：

```python
class Module:
    # 声明前置依赖模块的类名列表（可选）
    prerequisite = []
    
    def __init__(self):
        '''WARNING: __init__会被自动加载器无参数调用，务必保证无参数调用'''
        pass
    
    def register(self, message_handler, event_handler, module_handler):
        '''
        模块的初始化函数，必须重写
        参数：
            message_handler: MessageHandler实例
            event_handler: EventHandler实例（通常与message_handler.event_handler相同）
            module_handler: ModuleHandler实例
        '''
        pass
    
    def unregister(self):
        '''模块的卸载函数，可选重写'''
        pass
```

#### 3.2.2 ModuleAttribute 类

`ModuleAttribute` 用于描述模块的元数据（当前版本未完全实现，预留扩展）：

```python
class ModuleAttribute:
    def __init__(self):
        self.name = str()            # 显示名称（如"Example Module"）
        self.register_name = str()   # 注册名称（如"example_module"）
        self.is_builtin = True       # 是否为内置模块
        self.prerequisite = []       # 前置依赖模块列表
        # 预留：版本、作者等信息
```

#### 3.2.3 ModuleHandler 类

`ModuleHandler` 是模块系统的核心管理器：

```python
class ModuleHandler:
    def __init__(self):
        self.__module = dict()           # register_name -> 模块实例
        self.__attribute = dict()        # register_name -> ModuleAttribute
        
        # 依赖管理相关
        self.graph: Dict[str, List[str]] = {}          # 依赖图
        self.reverse_graph: Dict[str, List[str]] = {}  # 反向依赖图
        self.in_degree: Dict[str, int] = {}            # 入度表
        self.modules_by_name: Dict[str, Any] = {}      # 类名 -> 模块实例
        self.loaded_modules = set()                     # 已加载模块集合
```

### 3.3 模块生命周期

#### 3.3.1 完整生命周期流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  扫描模块    │───▶│  实例化模块  │───▶│  解析依赖    │───▶│  拓扑排序    │
└─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘
                                                                 │
                                                                 ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  注册模块    │◀───│  调用register│◀───│  按序加载    │◀───│  初始化顺序    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                 │
                                                                 ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  运行中      │───▶│  处理事件    │───▶│  提供服务    │───▶│  与其他模块交互 │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                 │
                                                                 ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  卸载模块    │◀───│  调用unregister│◀───│  依赖分析    │◀───│  卸载请求    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

#### 3.3.2 加载过程详解

1. **扫描模块**：`scan_module()` 函数扫描 `module_list` 目录
2. **实例化模块**：创建所有模块的实例
3. **构建依赖图**：根据 `prerequisite` 构建模块依赖关系
4. **拓扑排序**：使用 Kahn 算法确定加载顺序
5. **按序初始化**：调用每个模块的 `register()` 方法
6. **注册模块**：将模块实例注册到 ModuleHandler

#### 3.3.3 卸载过程详解

1. **依赖分析**：检查是否有其他模块依赖要卸载的模块
2. **卸载依赖模块**：递归卸载依赖该模块的所有模块（强制卸载时）
3. **调用 unregister**：执行模块的清理逻辑
4. **移除引用**：从所有数据结构中移除模块引用

### 3.4 模块依赖管理

#### 3.4.1 依赖声明

模块通过 `prerequisite` 类属性声明依赖：

```python
class DatabaseModule(Module):
    """数据库模块，无依赖"""
    pass

class UserModule(Module):
    """用户模块，依赖数据库模块"""
    prerequisite = ['DatabaseModule']
    
class AuthModule(Module):
    """认证模块，依赖用户模块和数据库模块"""
    prerequisite = ['UserModule', 'DatabaseModule']
```

#### 3.4.2 依赖解析算法

ModuleHandler 使用**拓扑排序**解析依赖关系：

```python
def load_module(self, module_dict, message_handler):
    # 1. 初始化数据结构
    for class_name, module_instance in module_dict.items():
        self.modules_by_name[class_name] = module_instance
        self.graph[class_name] = []
        self.reverse_graph[class_name] = []
        self.in_degree[class_name] = 0
    
    # 2. 构建依赖图
    for class_name, module_instance in module_dict.items():
        try:
            prerequisites = module_instance.prerequisite
        except:
            prerequisites = []
        
        for prereq in prerequisites:
            if prereq in self.graph:
                # prereq -> class_name 的依赖关系
                self.graph[prereq].append(class_name)
                # 反向依赖：class_name 依赖于 prereq
                self.reverse_graph[class_name].append(prereq)
                self.in_degree[class_name] += 1
    
    # 3. 拓扑排序（Kahn算法）
    queue = deque([class_name for class_name, degree in self.in_degree.items() if degree == 0])
    load_order: List[str] = []
    
    while queue:
        current = queue.popleft()
        load_order.append(current)
        
        # 减少依赖当前模块的其他模块的入度
        for dependent in self.graph[current]:
            self.in_degree[dependent] -= 1
            if self.in_degree[dependent] == 0:
                queue.append(dependent)
    
    # 4. 检查循环依赖
    if len(load_order) != len(module_dict):
        remaining = [class_name for class_name, degree in self.in_degree.items() if degree > 0]
        raise RuntimeError(f"发现循环依赖，涉及模块: {remaining}")
    
    # 5. 按顺序初始化模块
    for class_name in load_order:
        # ... 初始化逻辑
```

#### 3.4.3 循环依赖检测

系统会自动检测循环依赖并抛出异常：

```python
# 错误示例：循环依赖
class ModuleA(Module):
    prerequisite = ['ModuleB']

class ModuleB(Module):
    prerequisite = ['ModuleA']  # 循环依赖！

# 错误信息：
# RuntimeError: 发现循环依赖，无法确定加载顺序。涉及模块: ['ModuleA', 'ModuleB']
```

### 3.5 模块间通信

#### 3.5.1 通过 ModuleHandler 访问其他模块

```python
class MyModule(Module):
    def register(self, message_handler, event_handler, module_handler):
        # 通过 module_handler 访问其他模块
        self.config = module_handler.config  # 访问配置模块
        self.llm = module_handler.llm        # 访问LLM模块
        
        # 或者通过 get_module_by_classname 方法
        config_module = module_handler.get_module_by_classname('config')
        
    async def some_method(self):
        # 使用其他模块的功能
        reply = await self.llm.call_llm("Hello")
```

#### 3.5.2 通过事件系统通信（推荐）

```python
class RequestModule(Module):
    """请求模块，发送请求事件"""
    
    async def make_request(self, context, data):
        # 创建事件上下文
        event_context = EventContext()
        event_context.message_handler = context.message_handler
        event_context.mod = context.mod
        
        # 创建自定义事件
        event = Event(
            CustomEventType.REQUEST_EVENT,
            event_context,
            data
        )
        
        # 分发事件
        await context.message_handler.listener_system.dispatch_event(event)

class ResponseModule(Module):
    """响应模块，监听请求事件"""
    
    def register(self, message_handler, event_handler, module_handler):
        # 注册自定义事件监听器
        message_handler.register_listener(
            self, CustomEventType.REQUEST_EVENT, 
            self.handle_request
        )
    
    async def handle_request(self, event, context):
        """处理请求事件"""
        data = event.data
        # 处理请求并可能发送响应事件
```

### 3.6 模块开发指南

#### 3.6.1 创建新模块

**步骤1：在 `module_list` 目录中创建新文件**

```
autowater/
├── module_list/
│   ├── __init__.py
│   ├── my_module.py     # ← 新建模块文件
│   ├── config.py
│   └── ...
```

**步骤2：编写模块代码**

```python
# module_list/my_module.py
from module import Module
from event import EventType

class MyModule(Module):
    """我的自定义模块"""
    
    # 声明依赖（可选）
    prerequisite = ['config', 'llm']
    
    def __init__(self):
        super().__init__()
        self.counter = 0  # 模块状态
    
    def register(self, message_handler, event_handler, module_handler):
        """模块初始化"""
        # 保存引用
        self.message_handler = message_handler
        self.module_handler = module_handler
        
        # 获取依赖模块
        self.config = module_handler.config
        self.llm_service = module_handler.llm
        
        # 注册事件监听器
        message_handler.register_listener(
            self, EventType.EVENT_RECV_MSG,
            self.on_message, priority=5
        )
        
        # 初始化模块状态
        print(f"MyModule 已加载，配置: {self.config.my_setting}")
    
    async def on_message(self, event, context):
        """处理消息事件"""
        message = event.data
        self.counter += 1
        
        if "hello" in str(message).lower():
            await context.message_handler.send_message(
                f"你好！这是我第{self.counter}次响应。",
                message.data.get('group_id')
            )
    
    def unregister(self):
        """模块卸载"""
        print(f"MyModule 被卸载，共处理了 {self.counter} 条消息")
        # 清理资源...
    
    # 模块自定义方法
    def get_statistics(self):
        """获取模块统计信息"""
        return {"message_count": self.counter}
```

#### 3.6.2 模块配置

**通过配置模块访问配置：**

```python
class ConfigurableModule(Module):
    prerequisite = ['config']
    
    def register(self, message_handler, event_handler, module_handler):
        self.config = module_handler.config
        
        # 访问配置项
        self.my_setting = getattr(self.config, 'my_module_setting', 'default')
        
        # 或者直接访问原始配置
        if hasattr(self.config, 'my_module'):
            self.settings = self.config.my_module
```

**在 `config.json` 中添加模块配置：**

```json
{
    // ... 其他配置
    "my_module_setting": "custom_value",
    "my_module": {
        "enabled": true,
        "response_template": "你好 {user}！",
        "max_responses_per_day": 100
    }
}
```

#### 3.6.3 模块间服务提供

**提供服务的模块：**

```python
class CalculatorModule(Module):
    """计算器服务模块"""
    
    def register(self, message_handler, event_handler, module_handler):
        # 注册到模块管理器，使其他模块可以访问
        # （通过module_handler.CalculatorModule访问）
        pass
    
    def add(self, a, b):
        """提供加法服务"""
        return a + b
    
    def multiply(self, a, b):
        """提供乘法服务"""
        return a * b
```

**使用服务的模块：**

```python
class MathUserModule(Module):
    """使用计算器服务的模块"""
    prerequisite = ['CalculatorModule']
    
    async def on_message(self, event, context):
        message = event.data
        content = str(message)
        
        if "计算" in content:
            # 使用计算器服务
            calculator = context.mod.CalculatorModule
            result = calculator.add(10, 20)
            
            await context.message_handler.send_message(
                f"计算结果: {result}",
                message.data.get('group_id')
            )
```

### 3.7 模块管理操作

#### 3.7.1 动态加载模块

```python
# 动态加载单个模块（高级用法）
async def load_module_dynamically(module_class, module_handler, message_handler):
    """动态加载模块"""
    try:
        # 创建模块实例
        instance = module_class()
        
        # 手动构建模块字典（模拟扫描过程）
        module_dict = {module_class.__name__: instance}
        
        # 加载模块
        module_handler.load_module(module_dict, message_handler)
        
        print(f"模块 {module_class.__name__} 动态加载成功")
        return True
    except Exception as e:
        print(f"动态加载失败: {e}")
        return False
```

#### 3.7.2 动态卸载模块

```python
# 通过 ModuleHandler 卸载模块
def unload_module_example(module_handler):
    # 卸载单个模块（非强制）
    unloaded = module_handler.unload_module('MyModule', force_unload=False)
    
    if unloaded:
        print(f"成功卸载: {unloaded}")
    else:
        print("卸载失败（可能有其他模块依赖）")
    
    # 强制卸载（同时卸载依赖该模块的所有模块）
    unloaded_force = module_handler.unload_module('MyModule', force_unload=True)
    print(f"强制卸载: {unloaded_force}")
    
    # 卸载所有模块
    all_unloaded = module_handler.unload_all()
    print(f"卸载所有模块: {all_unloaded}")
```

#### 3.7.3 查询模块信息

```python
def inspect_modules(module_handler):
    """检查模块信息"""
    
    # 获取已加载模块列表
    loaded = module_handler.loaded_modules
    print(f"已加载模块: {loaded}")
    
    # 查询模块依赖关系
    for module_name in loaded:
        deps = module_handler.get_module_dependencies(module_name)
        print(f"模块 {module_name}:")
        print(f"  依赖: {deps.get('dependencies', [])}")
        print(f"  被依赖: {deps.get('dependents', [])}")
    
    # 检查模块是否可以安全卸载
    for module_name in loaded:
        safe = module_handler.is_safe_to_unload(module_name)
        print(f"模块 {module_name} 可安全卸载: {safe}")
```

### 3.8 最佳实践

#### 3.8.1 模块设计原则

1. **单一职责**：每个模块只负责一个明确的功能
2. **明确依赖**：清晰声明所有前置依赖
3. **状态管理**：合理管理模块内部状态
4. **资源清理**：在 `unregister` 中释放所有资源
5. **错误处理**：模块内部处理异常，避免影响系统

#### 3.8.2 性能优化建议

```python
class OptimizedModule(Module):
    """优化示例模块"""
    
    def __init__(self):
        # 延迟初始化 heavy_resource
        self.heavy_resource = None
    
    def register(self, message_handler, event_handler, module_handler):
        # 轻量级初始化
        self.message_handler = message_handler
        
        # 延迟加载 heavy_resource
        # 在实际需要时才初始化
    
    async def on_message(self, event, context):
        # 按需初始化 heavy_resource
        if self.heavy_resource is None:
            self.heavy_resource = self._init_heavy_resource()
        
        # 使用 heavy_resource
        result = self.heavy_resource.process(event.data)
    
    def _init_heavy_resource(self):
        """初始化耗时资源"""
        print("正在初始化 heavy_resource...")
        # 模拟耗时操作
        import time
        time.sleep(2)
        return {"initialized": True}
    
    def unregister(self):
        # 清理 heavy_resource
        if self.heavy_resource:
            self.heavy_resource.cleanup()
            self.heavy_resource = None
```

#### 3.8.3 调试技巧

```python
class DebugModule(Module):
    """调试辅助模块"""
    
    def register(self, message_handler, event_handler, module_handler):
        # 保存所有模块引用以便调试
        self.all_modules = module_handler
        
        # 注册调试事件
        message_handler.register_listener(
            self, EventType.EVENT_RECV_MSG,
            self.debug_handler, priority=999
        )
    
    async def debug_handler(self, event, context):
        """调试所有消息"""
        # 检查模块状态
        print(f"已加载模块数: {len(self.all_modules.loaded_modules)}")
        
        # 检查消息处理历史
        print(f"事件历史: {event.history}")
        
        # 模拟性能监控
        import time
        start_time = time.time()
        # ... 处理逻辑
        elapsed = time.time() - start_time
        if elapsed > 1.0:  # 超过1秒
            print(f"警告: 处理耗时 {elapsed:.2f} 秒")
```

### 3.9 常见问题与解决方案

#### 3.9.1 模块加载失败

**问题**：模块依赖未满足或循环依赖

**解决方案**：
```python
# 1. 检查 prerequisite 声明
class MyModule(Module):
    prerequisite = ['ExistingModule']  # 确保模块存在
    
# 2. 使用 try-except 处理可选依赖
def register(self, message_handler, event_handler, module_handler):
    try:
        self.optional_module = module_handler.OptionalModule
    except AttributeError:
        print("警告: OptionalModule 未加载，使用降级逻辑")
        self.optional_module = None
```

#### 3.9.2 模块初始化顺序问题

**问题**：模块A需要模块B的数据，但B还未初始化

**解决方案**：
```python
# 使用事件延迟初始化
class ModuleA(Module):
    def register(self, message_handler, event_handler, module_handler):
        # 只做最小初始化
        self.message_handler = message_handler
        self.initialized = False
        
        # 监听系统初始化完成事件
        message_handler.register_listener(
            self, EventType.EVENT_INIT,
            self.on_system_init, priority=0
        )
    
    async def on_system_init(self, event, context):
        """系统初始化完成后执行完整初始化"""
        # 此时所有模块都已加载
        self.module_b = context.mod.ModuleB
        self.initialized = True
```

#### 3.9.3 资源竞争问题

**问题**：多个模块同时访问共享资源

**解决方案**：
```python
import asyncio

class SharedResourceModule(Module):
    def __init__(self):
        self.lock = asyncio.Lock()
        self.shared_data = {}
    
    async def update_data(self, key, value):
        """安全更新共享数据"""
        async with self.lock:
            self.shared_data[key] = value
    
    async def get_data(self, key):
        """安全读取共享数据"""
        async with self.lock:
            return self.shared_data.get(key)
```

### 3.10 模块示例集合

#### 3.10.1 简单回复模块

```python
class SimpleReplyModule(Module):
    """简单自动回复模块"""
    
    def register(self, message_handler, event_handler, module_handler):
        message_handler.register_listener(
            self, EventType.EVENT_RECV_MSG,
            self.on_message
        )
        self.reply_count = 0
    
    async def on_message(self, event, context):
        message = event.data
        content = str(message).lower()
        
        replies = {
            "早上好": ["早上好！", "新的一天开始啦"],
            "晚安": ["晚安，好梦", "早点休息哦"],
            "谢谢": ["不客气！", "应该的"]
        }
        
        for keyword, reply_list in replies.items():
            if keyword in content:
                self.reply_count += 1
                reply = random.choice(reply_list)
                await context.message_handler.send_message(
                    reply, message.data.get('group_id')
                )
                break
```

#### 3.10.2 数据统计模块

```python
class StatisticsModule(Module):
    """消息统计模块"""
    
    prerequisite = ['config']
    
    def __init__(self):
        self.user_stats = {}  # user_id -> count
        self.total_messages = 0
    
    def register(self, message_handler, event_handler, module_handler):
        message_handler.register_listener(
            self, EventType.EVENT_RECV_MSG,
            self.record_message, priority=100  # 最后执行
        )
        
        # 从文件加载历史统计
        self.load_stats()
    
    async def record_message(self, event, context):
        """记录消息统计"""
        message = event.data
        user_id = message.user_id
        
        # 更新统计
        self.user_stats[user_id] = self.user_stats.get(user_id, 0) + 1
        self.total_messages += 1
        
        # 定期保存
        if self.total_messages % 100 == 0:
            self.save_stats()
    
    def get_top_users(self, n=10):
        """获取最活跃的用户"""
        sorted_users = sorted(
            self.user_stats.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        return sorted_users[:n]
    
    def load_stats(self):
        """从文件加载统计"""
        try:
            with open('data/statistics.json', 'r') as f:
                data = json.load(f)
                self.user_stats = data.get('user_stats', {})
                self.total_messages = data.get('total_messages', 0)
        except FileNotFoundError:
            pass
    
    def save_stats(self):
        """保存统计到文件"""
        data = {
            'user_stats': self.user_stats,
            'total_messages': self.total_messages
        }
        with open('data/statistics.json', 'w') as f:
            json.dump(data, f)
    
    def unregister(self):
        """模块卸载时保存统计"""
        self.save_stats()
```

### 3.11 总结

AutoWater 的模块系统提供了一个强大而灵活的插件架构：

1. **声明式依赖管理**：自动解决模块依赖关系
2. **动态生命周期**：支持运行时加载和卸载
3. **模块间通信**：通过 ModuleHandler 和事件系统协作
4. **易于扩展**：只需继承 Module 类并实现 register 方法

通过合理使用模块系统，开发者可以构建出高度模块化、可维护、可扩展的机器人应用。每个模块都可以独立开发、测试和部署，大大提高了开发效率和代码质量。

---

*下一部分将介绍消息系统的设计和高级用法。*

# AutoWater 开发者文档

## 第四部分：消息系统的设计与用法

### 4.1 消息系统概述

AutoWater 的消息系统负责处理QQ消息的**接收、解析、封装和发送**。系统设计目标是：

1. **统一消息模型**：提供一致的API处理各种消息类型
2. **组件化设计**：支持文本、@、图片、回复等消息组件
3. **双向转换**：实现原始JSON ↔ 消息对象的相互转换
4. **异步发送**：支持异步消息发送，提高并发性能

### 4.2 核心组件详解

#### 4.2.1 MessageComponent 类

`MessageComponent` 是消息的基本组成单元：

```python
class MessageComponent:
    def __init__(self, *args):
        """
        多种初始化方式：
        1. MessageComponent('text', 'Hello')         # 类型 + 数据
        2. MessageComponent(('text', 'Hello'))       # 元组形式
        3. MessageComponent('Hello')                 # 纯文本
        4. MessageComponent(other_component)         # 复制构造
        """
        
    def __str__(self):
        """用户友好的字符串表示"""
        if self.type == 'text':
            return self.data
        elif self.type == 'at':
            return f'@{self.data}'
        elif self.type == 'image':
            return '[图片]'
        elif self.type == 'reply':
            return f'回复消息id{self.data}'
```

**支持的消息类型**：
- `text`：文本消息，data为字符串
- `at`：@某人，data为QQ号
- `reply`：回复消息，data为消息ID
- `image`：图片，data为图片信息（暂未完全实现）

#### 4.2.2 Message 类

`Message` 类封装完整的消息信息：

```python
class Message:
    inner_count = 0  # 内部消息ID计数器
    
    def __init__(self, *args):
        """
        多种初始化方式：
        1. Message()                          # 空消息
        2. Message('Hello')                   # 纯文本消息
        3. Message(existing_message)          # 复制构造
        4. Message(payload_dict)              # 直接传入payload
        5. Message([component1, component2])  # 组件列表
        6. Message(user_id, msg_id, nickname, data)  # 完整消息数据
        """
```

**主要属性**：
- `content`：消息组件列表
- `user_id`：发送者QQ
- `message_id`：消息ID
- `nickname`：发送者昵称
- `data`：原始消息数据
- `payload`：发送用payload
- `has_group_id`：是否已设置群ID

### 4.3 消息生命周期

#### 4.3.1 消息处理完整流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  接收原始数据  │───▶│  创建Message │───▶│  解析组件    │───▶│  触发事件    │
│  (JSON格式)  │    │  对象        │    │  (parse_message)│   │  (dispatch)  │
└─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘
                                                                 │
                                                                 ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  模块处理    │◀───│  获取消息内容  │◀───│  遍历组件    │◀───│  事件监听器  │
│             │    │  (__str__)  │    │  (get_components)│   │             │
└─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘
                                                                 │
                                                                 ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  生成回复    │───▶│  构建Message │───▶│  生成payload │───▶│  发送消息    │
│             │    │  对象        │    │  (update_payload)│   │  (send_message)│
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

#### 4.3.2 消息接收与解析

```python
# process_message 方法中的解析逻辑
async def process_message(self, data):
    if data.get("post_type") == "message" and data.get("message_type") == "group":
        # 提取基本信息
        user_id = data["user_id"]
        message_id = data.get("message_id")
        nickname = data.get("sender", {}).get("card") or data.get("sender", {}).get("nickname", "")
        
        # 创建Message对象
        message = Message(user_id, message_id, nickname, data)
        
        # 解析消息组件
        # parse_message() 会被自动调用
```

#### 4.3.3 消息组件解析

```python
def parse_message(self):
    """从原始数据解析消息组件"""
    if self.data.get("message"):
        for raw_component in self.data["message"]:
            if raw_component['type'] == 'text':
                self.content.append(MessageComponent('text', raw_component['data']['text']))
            elif raw_component['type'] == 'at':
                self.content.append(MessageComponent('at', raw_component['data']['qq']))
            elif raw_component['type'] == 'reply':
                # 注意：这里有一个bug，应该是 'reply' 而不是 'at'
                self.content.append(MessageComponent('reply', raw_component['data']['id']))
            # 可以扩展支持更多类型：image, face, record等
```

### 4.4 消息发送系统

#### 4.4.1 MessageHandler 发送方法

`MessageHandler` 提供了多种消息发送方法：

```python
class MessageHandler:
    async def send_message_single_group(self, text: str | Message, group_id: str | int):
        """发送消息到单个群"""
        pass
    
    async def send_message_groups(self, text: str | Message, group_ids: Iterable):
        """发送消息到多个群"""
        pass
    
    async def send_message(self, text: str | Message, group_id: None | int | str | Iterable = None):
        """
        通用发送方法：
        - group_id=None: 发送到所有配置的群
        - group_id=123: 发送到指定群
        - group_id=[123, 456]: 发送到多个群
        """
        pass
    
    async def send_poke(self, user_id, group_id: None | int | str | Iterable = None):
        """发送戳一戳"""
        pass
    
    async def send_emoji_like(self, message_id, emoji_id):
        """给消息贴表情"""
        pass
    
    async def send_message_list(self, send_list, group_id: None | int | str | Iterable = None):
        """发送消息列表（多条消息）"""
        pass
```

#### 4.4.2 Payload 生成机制

```python
def update_payload(self):
    """生成发送用的payload"""
    self.payload = {
        "action": "send_group_msg",
        "params": {
            "group_id": -1,  # 占位符，实际发送时会替换
            "message": []
        }
    }
    
    for msg_component in self.content:
        if msg_component.type == 'text':
            self.payload["params"]["message"].append({
                "type": "text",
                "data": {"text": msg_component.data}
            })
        elif msg_component.type == 'at':
            self.payload["params"]["message"].append({
                "type": "at",
                "data": {"qq": str(msg_component.data)}
            })
        elif msg_component.type == 'reply':
            self.payload["params"]["message"].append({
                "type": "reply",
                "data": {"id": str(msg_component.data)}
            })
```

### 4.5 消息构建与使用

#### 4.5.1 基本消息构建

```python
# 1. 纯文本消息
msg1 = Message("Hello, World!")

# 2. 使用组件列表
msg2 = Message([
    ("reply", 123456),      # 回复消息ID 123456
    ("at", 987654321),      # @用户 987654321
    " 这是一条回复消息"       # 文本内容（注意空格）
])

# 3. 链式构建（推荐）
from message_utils import MessageComponent as MC

components = [
    MC('reply', 123456),
    MC('at', 987654321),
    MC('text', ' 你好！')
]
msg3 = Message(components)

# 4. 复制现有消息
original_msg = Message("Original")
copy_msg = Message(original_msg)
```

#### 4.5.2 复杂消息构建

```python
def build_complex_message():
    """构建复杂消息示例"""
    # 组合多种组件
    message = Message([
        ("reply", 123456789),           # 回复某条消息
        ("at", 987654321),              # @某人
        " 我看到了你的消息，",            # 文本1
        ("at", 111111111),              # 再@另一个人
        " 也来看看吧！\n",              # 文本2（带换行）
        "这是一条多行消息\n",
        "第二行内容"
    ])
    return message

# 或者使用逐步构建的方式
def build_message_step_by_step():
    """逐步构建消息"""
    components = []
    
    # 添加回复组件
    components.append(MessageComponent('reply', 123456))
    
    # 添加@组件
    components.append(MessageComponent('at', 987654321))
    
    # 添加文本组件
    components.append(MessageComponent('text', ' 你好！'))
    
    # 创建消息
    return Message(components)
```

#### 4.5.3 消息内容访问

```python
# 获取完整文本
message = Message([("at", 123456), " 你好！"])
text = str(message)  # "@123456 你好！"

# 遍历消息组件
for component in message.get_components():
    print(f"类型: {component.type}, 数据: {component.data}")
    # 输出:
    # 类型: at, 数据: 123456
    # 类型: text, 数据: " 你好！"

# 检查是否包含特定组件
def has_at_component(message, qq_id=None):
    """检查消息是否包含@组件"""
    for component in message.get_components():
        if component.type == 'at':
            if qq_id is None or component.data == qq_id:
                return True
    return False

# 提取纯文本（去除@和回复等组件）
def extract_pure_text(message):
    """提取纯文本内容"""
    texts = []
    for component in message.get_components():
        if component.type == 'text':
            texts.append(component.data)
    return ''.join(texts)
```

### 4.6 高级消息功能

#### 4.6.1 消息模板系统

```python
class MessageTemplate:
    """消息模板系统"""
    
    @staticmethod
    def reply_to(user_id, message_id, text):
        """构建回复某人的消息"""
        return Message([
            ("reply", message_id),
            ("at", user_id),
            f" {text}"
        ])
    
    @staticmethod
    def mention_all(text):
        """构建@所有人的消息"""
        return Message([
            ("at", "all"),
            f" {text}"
        ])
    
    @staticmethod
    def multi_line(lines):
        """构建多行消息"""
        return Message("\n".join(lines))
    
    @staticmethod
    def format(template, **kwargs):
        """格式化消息模板"""
        return Message(template.format(**kwargs))

# 使用示例
async def send_formatted_reply(context, original_msg, response_text):
    """发送格式化回复"""
    template = MessageTemplate.reply_to(
        original_msg.user_id,
        original_msg.message_id,
        response_text
    )
    await context.message_handler.send_message(
        template,
        original_msg.data.get('group_id')
    )
```

#### 4.6.2 消息条件发送

```python
class ConditionalSender:
    """条件发送器"""
    
    def __init__(self, message_handler):
        self.message_handler = message_handler
        self.send_history = {}  # 发送历史记录
    
    async def send_if(self, condition, message, group_id, cooldown=0):
        """
        条件发送消息
        condition: 条件函数或布尔值
        cooldown: 冷却时间（秒）
        """
        # 检查冷却
        key = f"{group_id}_{str(message)}"
        last_sent = self.send_history.get(key, 0)
        current_time = time.time()
        
        if current_time - last_sent < cooldown:
            return False
        
        # 检查条件
        if callable(condition):
            should_send = await condition()
        else:
            should_send = condition
        
        if should_send:
            await self.message_handler.send_message(message, group_id)
            self.send_history[key] = current_time
            return True
        
        return False
```

#### 4.6.3 消息队列与限流

```python
import asyncio
from collections import deque

class MessageQueue:
    """消息队列，支持限流"""
    
    def __init__(self, message_handler, rate_limit=1.0):
        """
        rate_limit: 消息发送速率（条/秒）
        """
        self.message_handler = message_handler
        self.rate_limit = rate_limit
        self.queue = deque()
        self.is_processing = False
        self.last_send_time = 0
    
    async def add_message(self, message, group_id):
        """添加消息到队列"""
        self.queue.append((message, group_id))
        if not self.is_processing:
            self.is_processing = True
            asyncio.create_task(self.process_queue())
    
    async def process_queue(self):
        """处理消息队列"""
        while self.queue:
            # 计算等待时间以确保限流
            current_time = time.time()
            time_since_last = current_time - self.last_send_time
            wait_time = max(0, 1.0 / self.rate_limit - time_since_last)
            
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            
            # 发送消息
            message, group_id = self.queue.popleft()
            try:
                await self.message_handler.send_message(message, group_id)
                self.last_send_time = time.time()
            except Exception as e:
                print(f"发送失败: {e}")
                # 可以选择重试或丢弃
        
        self.is_processing = False
```

### 4.7 消息处理模式

#### 4.7.1 命令模式处理

```python
class CommandProcessor(Module):
    """命令处理器"""
    
    def register(self, message_handler, event_handler, module_handler):
        message_handler.register_listener(
            self, EventType.EVENT_RECV_MSG,
            self.process_command, priority=1  # 高优先级
        )
        self.commands = {
            "帮助": self.cmd_help,
            "状态": self.cmd_status,
            "设置": self.cmd_settings,
        }
    
    async def process_command(self, event, context):
        message = event.data
        text = str(message).strip()
        
        # 检查命令前缀（例如 "!"）
        if text.startswith("!"):
            command = text[1:].split()[0]  # 提取命令
            args = text[1:].split()[1:]    # 提取参数
            
            if command in self.commands:
                # 执行命令
                await self.commands[command](context, message, args)
                
                # 阻止其他模块处理（可选）
                # event.block_event()
                return True
        
        return False
    
    async def cmd_help(self, context, message, args):
        """帮助命令"""
        help_text = "可用命令：\n"
        help_text += "!帮助 - 显示此帮助信息\n"
        help_text += "!状态 - 查看机器人状态\n"
        help_text += "!设置 - 更改设置\n"
        
        await context.message_handler.send_message(
            MessageTemplate.reply_to(
                message.user_id,
                message.message_id,
                help_text
            ),
            message.data.get('group_id')
        )
    
    async def cmd_status(self, context, message, args):
        """状态命令"""
        status = "机器人运行正常\n"
        status += f"已加载模块: {len(context.mod.loaded_modules)}\n"
        status += f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        await context.message_handler.send_message(
            MessageTemplate.reply_to(
                message.user_id,
                message.message_id,
                status
            ),
            message.data.get('group_id')
        )
```

#### 4.7.2 消息过滤器

```python
class MessageFilter(Module):
    """消息过滤器"""
    
    def register(self, message_handler, event_handler, module_handler):
        message_handler.register_listener(
            self, EventType.EVENT_RECV_MSG,
            self.filter_messages, priority=0  # 最高优先级
        )
        self.banned_words = ["敏感词1", "敏感词2", "广告"]
        self.banned_users = [123456789]  # 黑名单用户
    
    async def filter_messages(self, event, context):
        message = event.data
        text = str(message).lower()
        
        # 检查黑名单用户
        if message.user_id in self.banned_users:
            print(f"拦截黑名单用户 {message.user_id} 的消息")
            event.block_event()
            return True
        
        # 检查敏感词
        for word in self.banned_words:
            if word in text:
                print(f"拦截包含敏感词 '{word}' 的消息")
                event.block_event()
                
                # 可选：发送警告
                warning = MessageTemplate.reply_to(
                    message.user_id,
                    message.message_id,
                    "请勿发送敏感内容"
                )
                await context.message_handler.send_message(
                    warning,
                    message.data.get('group_id')
                )
                return True
        
        return False
```

#### 4.7.3 消息统计与分析

```python
class MessageAnalyzer(Module):
    """消息分析器"""
    
    def register(self, message_handler, event_handler, module_handler):
        message_handler.register_listener(
            self, EventType.EVENT_RECV_MSG,
            self.analyze_message, priority=100  # 低优先级
        )
        self.word_count = {}
        self.user_activity = {}
        self.total_messages = 0
    
    async def analyze_message(self, event, context):
        message = event.data
        text = str(message)
        
        # 更新统计
        self.total_messages += 1
        self.user_activity[message.user_id] = self.user_activity.get(message.user_id, 0) + 1
        
        # 分词统计
        words = text.split()
        for word in words:
            if len(word) > 1:  # 忽略单字
                self.word_count[word] = self.word_count.get(word, 0) + 1
        
        # 定期输出统计结果
        if self.total_messages % 100 == 0:
            await self.report_statistics(context, message.data.get('group_id'))
    
    async def report_statistics(self, context, group_id):
        """报告统计结果"""
        # 找出最活跃的用户
        top_users = sorted(
            self.user_activity.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # 找出最常用的词
        top_words = sorted(
            self.word_count.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        report = f"📊 统计报告（最近 {self.total_messages} 条消息）\n"
        report += "最活跃用户：\n"
        for user_id, count in top_users:
            report += f"  - {user_id}: {count} 条\n"
        
        report += "\n最常用词汇：\n"
        for word, count in top_words:
            report += f"  - {word}: {count} 次\n"
        
        await context.message_handler.send_message(
            Message(report),
            group_id
        )
```

### 4.8 消息扩展开发

#### 4.8.1 添加新消息类型

```python
# 扩展 MessageComponent 支持新类型
class ExtendedMessageComponent(MessageComponent):
    def __str__(self):
        # 调用父类方法
        if self.type in ['text', 'at', 'reply', 'image']:
            return super().__str__()
        
        # 添加新类型
        if self.type == 'face':
            return f'[表情:{self.data}]'
        elif self.type == 'record':
            return '[语音消息]'
        elif self.type == 'forward':
            return '[合并转发]'
        else:
            return f'[{self.type}消息]'

# 扩展 Message 的 parse_message 方法
class ExtendedMessage(Message):
    def parse_message(self):
        super().parse_message()  # 调用父类解析
        
        if self.data.get("message"):
            for raw_component in self.data["message"]:
                if raw_component['type'] == 'face':
                    # QQ表情
                    self.content.append(
                        MessageComponent('face', raw_component['data']['id'])
                    )
                elif raw_component['type'] == 'record':
                    # 语音消息
                    self.content.append(
                        MessageComponent('record', raw_component['data']['file'])
                    )
                elif raw_component['type'] == 'forward':
                    # 合并转发
                    self.content.append(
                        MessageComponent('forward', raw_component['data']['id'])
                    )
    
    def update_payload(self):
        """扩展payload生成"""
        super().update_payload()  # 调用父类方法
        
        # 清空并重新构建以包含新类型
        self.payload["params"]["message"] = []
        
        for msg_component in self.content:
            if msg_component.type == 'face':
                self.payload["params"]["message"].append({
                    "type": "face",
                    "data": {"id": msg_component.data}
                })
            elif msg_component.type == 'record':
                self.payload["params"]["message"].append({
                    "type": "record",
                    "data": {"file": msg_component.data}
                })
            elif msg_component.type == 'forward':
                self.payload["params"]["message"].append({
                    "type": "forward",
                    "data": {"id": msg_component.data}
                })
            else:
                # 原有类型的处理
                super()._add_component_to_payload(msg_component)
```

#### 4.8.2 消息序列化与持久化

```python
import json
from datetime import datetime

class MessageSerializer:
    """消息序列化器"""
    
    @staticmethod
    def serialize(message):
        """序列化消息对象"""
        return {
            'timestamp': datetime.now().isoformat(),
            'user_id': message.user_id,
            'message_id': message.message_id,
            'nickname': message.nickname,
            'content': [
                {'type': c.type, 'data': c.data}
                for c in message.content
            ],
            'raw_data': message.data,
            'group_id': message.data.get('group_id') if message.data else None
        }
    
    @staticmethod
    def deserialize(data):
        """反序列化为消息对象"""
        # 创建消息对象
        msg = Message()
        msg.user_id = data['user_id']
        msg.message_id = data['message_id']
        msg.nickname = data['nickname']
        msg.data = data['raw_data']
        
        # 重建消息组件
        msg.content = [
            MessageComponent(c['type'], c['data'])
            for c in data['content']
        ]
        
        return msg
    
    @staticmethod
    def save_to_file(messages, filename):
        """保存消息列表到文件"""
        serialized = [MessageSerializer.serialize(msg) for msg in messages]
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serialized, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def load_from_file(filename):
        """从文件加载消息列表"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [MessageSerializer.deserialize(item) for item in data]
        except FileNotFoundError:
            return []
```

### 4.9 调试与问题排查

#### 4.9.1 消息调试工具

```python
class MessageDebugger(Module):
    """消息调试器"""
    
    def register(self, message_handler, event_handler, module_handler):
        message_handler.register_listener(
            self, EventType.EVENT_RECV_MSG,
            self.debug_incoming, priority=999
        )
        message_handler.register_listener(
            self, EventType.EVENT_PRE_SEND_MSG,
            self.debug_outgoing, priority=999
        )
    
    async def debug_incoming(self, event, context):
        """调试接收的消息"""
        message = event.data
        print("\n" + "="*50)
        print("📥 收到消息")
        print(f"发件人: {message.nickname}({message.user_id})")
        print(f"消息ID: {message.message_id}")
        print(f"群号: {message.data.get('group_id')}")
        print(f"原始数据: {json.dumps(message.data, indent=2, ensure_ascii=False)}")
        print(f"解析结果: {message}")
        print("消息组件:")
        for i, component in enumerate(message.content):
            print(f"  [{i}] {component.type}: {component.data}")
        print("="*50)
    
    async def debug_outgoing(self, event, context):
        """调试发送的消息"""
        message = event.data
        print("\n" + "="*50)
        print("📤 发送消息")
        print(f"Payload: {json.dumps(message.payload, indent=2, ensure_ascii=False)}")
        print(f"内容: {message}")
        print("="*50)
```

#### 4.9.2 常见问题与解决

**问题1：消息发送失败**

```python
async def safe_send_message(message_handler, message, group_id, retries=3):
    """安全发送消息，支持重试"""
    for attempt in range(retries):
        try:
            await message_handler.send_message(message, group_id)
            return True
        except Exception as e:
            print(f"发送失败 (尝试 {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)  # 指数退避
    return False
```

**问题2：消息解析错误**

```python
def validate_message_data(data):
    """验证消息数据格式"""
    required_fields = ['post_type', 'message_type', 'user_id']
    for field in required_fields:
        if field not in data:
            return False, f"缺少必要字段: {field}"
    
    if data['post_type'] == 'message':
        if 'message' not in data:
            return False, "消息数据缺少message字段"
    
    return True, "数据格式正确"
```

**问题3：消息ID冲突**

```python
# Message 类的内部ID管理优化
class Message:
    inner_count = 0
    _lock = asyncio.Lock()  # 添加锁避免并发问题
    
    def __init__(self, *args):
        # ... 其他初始化逻辑
        
        async with self._lock:
            self.message_id = Message.inner_count
            Message.inner_count -= 1
```

### 4.10 最佳实践

#### 4.10.1 消息构建最佳实践

```python
# 1. 使用辅助函数构建复杂消息
def build_well_formatted_reply(original_msg, reply_text):
    """构建格式良好的回复消息"""
    # 确保回复文本前有空格
    if not reply_text.startswith(' '):
        reply_text = ' ' + reply_text
    
    return Message([
        ("reply", original_msg.message_id),
        ("at", original_msg.user_id),
        reply_text
    ])

# 2. 避免消息过长
async def send_long_message_safely(context, text, group_id, max_length=500):
    """安全发送长消息，自动分割"""
    if len(text) <= max_length:
        await context.message_handler.send_message(text, group_id)
    else:
        # 分割消息
        chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        for chunk in chunks:
            await context.message_handler.send_message(chunk, group_id)
            await asyncio.sleep(0.5)  # 避免发送过快

# 3. 合理使用消息组件
def build_rich_message():
    """构建富文本消息示例"""
    return Message([
        ("reply", 123456),
        ("at", 987654321),
        " 这是重要通知：\n",
        "📢 第一点：...\n",
        "🔔 第二点：...\n",
        "✅ 第三点：...\n",
        "\n",
        "请相关人员注意！"
    ])
```

#### 4.10.2 性能优化建议

```python
class OptimizedMessageHandler:
    """优化版消息处理器"""
    
    def __init__(self, websocket, module_handler):
        self.websocket = websocket
        self.module_handler = module_handler
        self.message_cache = {}  # 消息缓存
        self.cache_size = 1000
    
    async def send_message_with_cache(self, message, group_id):
        """带缓存的消息发送，避免重复发送相同消息"""
        cache_key = f"{group_id}_{hash(str(message))}"
        
        if cache_key in self.message_cache:
            print("消息已在缓存中，跳过发送")
            return
        
        await self.send_message(message, group_id)
        
        # 更新缓存
        self.message_cache[cache_key] = time.time()
        
        # 清理过期缓存
        if len(self.message_cache) > self.cache_size:
            self._cleanup_cache()
    
    def _cleanup_cache(self):
        """清理缓存"""
        # 保留最近使用的缓存项
        sorted_items = sorted(
            self.message_cache.items(),
            key=lambda x: x[1],
            reverse=True
        )[:self.cache_size // 2]
        
        self.message_cache = dict(sorted_items)
```

### 4.11 总结

AutoWater 的消息系统提供了一个完整、灵活的消息处理框架：

1. **统一的消息模型**：`Message` 和 `MessageComponent` 封装了所有消息操作
2. **双向转换能力**：支持原始数据 ↔ 消息对象的相互转换
3. **丰富的发送接口**：提供多种发送方式和高级功能
4. **强大的扩展性**：易于添加新消息类型和处理逻辑
5. **完善的调试支持**：提供详细的调试工具和错误处理

通过合理使用消息系统，开发者可以轻松处理各种复杂的消息场景，构建出功能丰富、稳定可靠的QQ机器人应用。

---

*下一部分将介绍配置系统的设计和高级用法。*