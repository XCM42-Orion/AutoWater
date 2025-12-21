import json
from enum import Enum
import asyncio
from collections.abc import Iterable
import random
from module import *
from event import *
import logger
from logger import Logger



class MessageComponent:
    def __init__(self, *args):
        if len(args) == 2:
            type = args[0]
            data = args[1]
            self.type = type
            self.data = data

        elif len(args) == 1:
            if isinstance(args[0],tuple):
                self.type = args[0][0]
                self.data = args[0][1]
            if isinstance(args[0],str):
                self.type = 'text'
                self.data = args[0]
            if isinstance(args[0],MessageComponent):
                self.type = args[0].type
                self.data = args[0].data

    

    def __str__(self):
        if self.type == 'reply':
            return '[回复信息id' + str(self.data) + ']'   #data->message_id
        elif self.type == 'image':
            return '[图片]'
        elif self.type == 'text':                 #data->str
            return self.data
        elif self.type == 'at':                   #data->qq_id
            return '[@' + str(self.data) + ']'
            


#定义消息对象

class Message:
    inner_count = 0
    def __init__(self, *args):
        if len(args) == 0:
            #消息组件
            self.content = []

            #来源数据
            self.user_id = -1
            self.message_id = Message.inner_count
            self.nickname = 'system'

            #消息原始数据（如果有）
            self.data = json.dumps({})
            self.payload = json.dumps({})

            #是否具有group_id
            self.has_group_id = False

            #id计数器--
            Message.inner_count -= 1
        elif len(args) == 1:
            if isinstance(args[0], str):  #传入纯文本初始化
                self.content = [MessageComponent('text', args[0])]


                self.user_id = -1
                self.nickname = 'system'
                self.message_id = Message.inner_count
                Message.inner_count -= 1

                self.update_payload()

                self.data = None
                self.has_group_id = False
            elif isinstance(args[0], Message): #传入Message对象初始化（复制构造）
                self.content = args[0].content

                self.user_id = args[0].user_id
                self.nickname = args[0].nickname
                self.payload = args[0].payload

                self.data = args[0].data
                self.has_group_id = args[0].has_group_id
                
            elif isinstance(args[0], dict):   #直接传入payload
                self.text = ''
                self.content = []
                self.payload = args[0]

                self.user_id = -1
                self.message_id = Message.inner_count
                Message.inner_count -= 1
                self.nickname = 'system'

                self.data = None
                self.has_group_id = False

            elif isinstance(args[0], list):   #一堆component组成的list初始化
                self.text = ''
                self.content = []
                for component in args[0]:
                    self.content.append(MessageComponent(component))

                self.update_payload()

                self.user_id = -1
                self.message_id = Message.inner_count
                Message.inner_count -= 1
                self.nickname = 'system'

                self.data = None
                self.has_group_id = False
        
        elif len(args) == 4: #传入完整消息数据初始化
            user_id, message_id, nickname, data = args

            self.user_id = user_id
            self.message_id = message_id
            self.nickname = nickname

            self.content = []

            self.data = data
            self.has_group_id = False
            self.parse_message()
            self.update_payload()
            

    def __str__(self):
        return ''.join([str(msg) for msg in self.content])
    
    def get_components(self):
        for component in self.content:   #返回一个迭代器
            yield component

    def __len__(self):
        return len(str(self))


    def update_payload(self):
        self.payload = {
            "action": "send_group_msg",
            "params": {
                "group_id": -1,
                "message": list()
                }
        }
        for msg_component in self.content:
            if msg_component.type == 'text':
                self.payload["params"]["message"].append({"type":"text","data":{"text":msg_component.data}})
            elif msg_component.type == 'at':
                self.payload["params"]["message"].append({"type":"at","data":{"qq":str(msg_component.data)}})
            elif msg_component.type == 'reply':
                self.payload["params"]["message"].append({"type":"reply","data":{"id":str(msg_component.data)}})


    def parse_message(self):
        if self.data.get("message"):
            for raw_component in self.data["message"]:
                if raw_component['type'] == 'text':
                    self.content.append(MessageComponent('text',raw_component['data']['text']))
                elif raw_component['type'] == 'at':
                    self.content.append(MessageComponent('at',raw_component['data']['qq']))
                elif raw_component['type'] == 'reply':
                    self.content.append(MessageComponent('at',raw_component['data']['id']))

class SystemModule(Module):
    pass

# 修改 MessageHandler 以使用优先级系统
class MessageHandler:
    def __init__(self, websocket, module_handler, target_groups):
        #self.config = config
        #self.llm_service = LLMService(config)
        # 使用新的优先级监听器系统
        self.event_handler = EventHandler(self)
        self.websocket = websocket
        self.group_ids = target_groups
        self.self_id = str()
        self.messages = dict()
        self.event_handler = EventHandler(self)
        self.module_handler = module_handler
        self.logger = Logger()
        self.target_groups = target_groups
        self.message_history = list()

        #发送信息时，以0优先级调用发送
        self.system_module = SystemModule()
        self.register_listener(self.system_module, EventType.EVENT_SEND_MSG, self._send_message)

    def start_message_handler(self):
        pass
    
    def register_listener(self, module: Module, event_type: EventType, listener: Callable, priority: int = 0):
        """注册监听器（封装方法）"""
        '''WARNING:priority越大越优先'''
        self.event_handler._inner_register_listener(module, event_type, listener, priority)

    

    async def dispatch_event(self, event_type: EventType, data: Any):
        """分发事件（封装方法）"""
        context = EventContext()

        context.message_handler = self
        context.event_handler = self.event_handler
        context.mod = self.module_handler

        event = Event(event_type, data)

        await self.event_handler.dispatch_event(event, context)

    async def _send_message(self, event, context):
        if logger.debug_flag:
            self.logger.debug("发送信息:" + str(event.data[1]))
            self.logger.warning("注意，现在debug_flag=True，消息发送已被拦截。若要启动消息发送，请在logger.py修改debug_flag为False")
        else:
            asyncio.create_task(self.websocket.send(json.dumps(event.data[1].payload)))
    
    async def _send_message_single_group(self, module: Module, text:str|Message, group_id: str|int,proxy=None):
        """发送消息到WebSocket"""
        #此处的proxy实际上是发送者的messagehandlerproxy
        if isinstance(text, str):
            message = Message(text)
            message.payload["params"]["group_id"] = group_id
            proxy.feedback(message)
            await self.dispatch_event(EventType.EVENT_SEND_MSG, (proxy.context_proxy, message))
        elif isinstance(text, Message):
            message = text
            if not message.has_group_id:
                message.payload["params"]["group_id"] = group_id
            proxy.feedback(message)
            await self.dispatch_event(EventType.EVENT_SEND_MSG, (proxy.context_proxy, message))
        return True
    
    async def _send_message_groups(self, module: Module, text:str|Message, group_ids: Iterable, proxy=None):
        message_tasks = [asyncio.create_task(self._send_message_single_group(module, text, group_id,proxy)) 
                         for group_id in group_ids]
        await asyncio.gather(*message_tasks)
        return True
    
    async def send_message(self, message:str|Message|Iterable, group_id:None|int|str|Iterable=None, proxy=None, module: Module = None):
        if not isinstance(message, List):
            message = [message]

        for text in message:
            if group_id is None:
                return await self._send_message_groups(module, text, self.group_ids,proxy)
            elif isinstance(group_id, Iterable):
                return await self._send_message_groups(module, text, group_id,proxy)
            else:
                return await self._send_message_single_group(module, text, group_id,proxy)
    
    async def send_poke(self, user_id, group_id:None|int|str|Iterable=None, proxy=None, module: Module = None):
        if group_id is None:
            group_id = random.choice(self.group_ids)
        payload = {
            "action": "send_poke",
            "params": {
                "user_id": user_id,
            }
        }
        await self.send_message(module, Message(payload), group_id, proxy)
        self.logger.info(f"已在群 {group_id}戳一戳用户 {user_id}")
        return True
    
    async def send_emoji_like(self, message_id, emoji_id, proxy=None,module: Module = None):
        payload = {
            "action": "set_msg_emoji_like",
            "params": {
                "message_id": message_id,
                "emoji_id": emoji_id
            }
        }
        await self.send_message(Message(payload), None, proxy, module)
        self.logger.info(f"已为消息 {message_id} 贴表情 {emoji_id}")
        return True
    
    def set_websocket(self, websocket):
        self.websocket = websocket
    
    async def process_message(self, data):
        """处理收到的消息"""
        accept_message_type = ['message'] if not logger.debug_flag else ['message', 'message_sent']
        if (data.get("post_type") in accept_message_type and data.get("message_type") == "group") or data.get("post_type") == "notice":       
            group_id = data.get("group_id")
            if group_id not in self.group_ids:
                return
            
            self.self_id = str(data.get("self_id"))
                
            user_id = data["user_id"]
            message_id = data.get("message_id")
            if data.get("sender") is None:
                nickname = ""
            else:
                nickname = data["sender"]["card"] or data["sender"]["nickname"]

            message = Message(user_id, message_id, nickname, data)
            self.messages[message_id] = message
            # 事件广播
            if data.get("post_type") in accept_message_type:
                #先打印日志，后分发事件，以免delay模块造成阻塞，影响用户体验
                self.logger.info(f"[\033[34m消息\033[0m][\033[34m群聊\033[0m][{data.get('group_name')}({group_id})]{nickname}({user_id})：{message}")
                await self.dispatch_event(EventType.EVENT_RECV_MSG, message)
            else:
                await self.dispatch_event(EventType.EVENT_NOTICE_MSG, message)
        else:
            return
'''
# 使用示例装饰器（可选）
def listener(event_type: EventType, priority: Priority = Priority.NORMAL):
    """监听器装饰器"""
    def decorator(func):
        func._listener_info = (event_type, priority)
        return func
    return decorator

def register_listeners_from_class(handler: MessageHandler, listener_class):
    """从类中自动注册监听器"""
    for attr_name in dir(listener_class):
        attr = getattr(listener_class, attr_name)
        if callable(attr) and hasattr(attr, '_listener_info'):
            event_type, priority = attr._listener_info
            handler.register_listener(event_type, attr, priority)'''
    
