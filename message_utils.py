import json
#from actions import ActionHandler
from llm_service import LLMService
from enum import Enum
import asyncio
from collections.abc import Iterable
import random

class EventType(Enum):
    EVENT_INIT = 0
    EVENT_RECV_MSG = 1
    EVENT_PRE_SEND_MSG = 2
    EVENT_NOTICE_MSG = 3

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
            return '回复信息id' + str(self.data)   #data->message_id
        elif self.type == 'image':
            return '[图片]'
        elif self.type == 'text':                 #data->str
            return self.data
        elif self.type == 'at':                   #data->qq_id
            return '@' + str(self.data)
            


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

    
    

class MessageHandler:
    def __init__(self, config, websocket):
        self.config = config
        #self.action_handler = ActionHandler(config)
        self.llm_service = LLMService(config)
        self.listeners = {}
        self.websocket = websocket
        self.group_ids = self.config.target_groups
        self.self_id = str()
        self.messages = dict()

    def register_listener(self, event_type, listener):
        self.listeners.setdefault(event_type, []).append(listener)

    async def dispatch_event(self, event_type, message):
        tasks = [l(self, message, self.config) if asyncio.iscoroutinefunction(l) else None 
                 for l in self.listeners.get(event_type,[])]
        await asyncio.gather(*(t for t in tasks if t))

    async def send_message_single_group(self, text:str|Message, group_id: str|int):
        """发送消息到WebSocket"""
        if isinstance(text, str):       #判断消息是text还是Message。所以这两种类型都可以发送。
            message = Message(text)
            message.payload["params"]["group_id"] = group_id
            await self.websocket.send(json.dumps(message.payload))
        elif isinstance(text, Message):
            message = text
            print(message.payload)
            if not message.has_group_id:
                message.payload["params"]["group_id"] = group_id
            await self.websocket.send(json.dumps(message.payload))

    async def send_message_groups(self, text:str|Message, group_ids: Iterable):
        message_tasks=[ asyncio.create_task(self.send_message_single_group(text,group_id)) for group_id in group_ids]
        await asyncio.gather(*message_tasks)

    async def send_message(self, text:str|Message, group_id:None|int|str|Iterable=None):
        #处理多种group_id格式
        if group_id is None:
            await self.send_message_groups(text,self.group_ids)
        elif isinstance(group_id, Iterable):
            await self.send_message_groups(text,group_id)
        else:
            await self.send_message_single_group(text,group_id)

        

    async def send_poke(self, user_id, group_id:None|int|str|Iterable=None):
        if group_id is None:
            group_id=random.choice(self.group_ids)
        payload = {
                "action": "send_poke",
                "params": {
                    "user_id": user_id,
                }
            }
        await self.send_message(Message(payload),group_id)

    async def send_emoji_like(self, message_id, emoji_id):
        payload = {
                    "action": "set_msg_emoji_like",
                    "params": {
                        "message_id": message_id,
                        "emoji_id": emoji_id
                    }
                }
        await self.send_message(Message(payload))

    async def send_message_list(self, send_list, group_id:None|int|str|Iterable=None):
        """发送消息列表"""
        for send_item in send_list:
            await self.send_message(Message(send_item),group_id)

    def set_websocket(self, websocket):
        self.websocket = websocket

    async def process_message(self, data):
        """处理收到的消息"""

        if (data.get("post_type") == "message" and data.get("message_type") == "group") or data.get("post_type") == "notice":       
            group_id = data.get("group_id")
            if group_id not in self.group_ids:
                return
            
            self.self_id = str(data.get("self_id"))
                
            # 提取消息内容
            #text = "".join(seg["data"]["text"] for seg in data["message"] if seg["type"] == "text")
            user_id = data["user_id"]
            message_id = data.get("message_id")
            if data.get("sender") is None:
                nickname = ""
            else:
                nickname = data["sender"]["card"] or data["sender"]["nickname"]

            message = Message(user_id, message_id, nickname, data)
            self.messages[message_id] = message

            # 事件广播
            if data.get("post_type") == "message":
                # 添加到历史记录
                self.llm_service.add_message_to_history(user_id, nickname, str(message))
                await self.dispatch_event(EventType.EVENT_RECV_MSG, message)
                print(f"{nickname}({user_id})：{message}")
            else:
                await self.dispatch_event(EventType.EVENT_NOTICE_MSG, message)
        else:
            return

