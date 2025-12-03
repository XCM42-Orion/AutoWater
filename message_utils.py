import json
#from actions import ActionHandler
from llm_service import LLMService
from enum import Enum
import asyncio

class EventType(Enum):
    EVENT_INIT = 0
    EVENT_RECV_MSG = 1
    EVENT_PRE_SEND_MSG = 2

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
                if self.type == 'at':
                    self.data = str(self.data)
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
            if isinstance(args[0], str):
                self.content = [MessageComponent('text', args[0])]


                self.user_id = str(-1)
                self.nickname = 'system'
                self.message_id = str(Message.inner_count)
                Message.inner_count -= 1

                self.update_payload()

                self.data = None
                self.has_group_id = False
            elif isinstance(args[0], Message):
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

                self.user_id = str(-1)
                self.message_id = str(Message.inner_count)
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
                self.message_id = str(Message.inner_count)
                Message.inner_count -= 1
                self.nickname = 'system'

                self.data = None
                self.has_group_id = False
            '''elif isinstance(args[0], list):
                self.text = ''
                self.content = []
                for component in args[0]:
                    self.content.append(MessageComponent(component))
                self.content = args[0]

                self.update_payload()

                self.user_id = -1
                self.message_id = Message.inner_count
                Message.inner_count -= 1
                self.nickname = 'system'

                self.data = None'''
        
        elif len(args) == 4:
            user_id, message_id, nickname, data = args

            self.user_id = str(user_id)
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
        self.group_id = self.config.target_groups[0]#临时代码
        self.self_id = str()
        self.messages = dict()

    def register_listener(self, event_type, listener):
        self.listeners.setdefault(event_type, []).append(listener)

    async def dispatch_event(self, event_type, message):
        tasks = [l(self, message, self.config) if asyncio.iscoroutinefunction(l) else None 
                 for l in self.listeners.get(event_type,[])]
        await asyncio.gather(*(t for t in tasks if t))

    '''async def send_message(self, ws, delay, payload):
        """发送消息到WebSocket"""
        await asyncio.sleep(delay)
        await self.websocket.send(json.dumps(payload))'''

    async def send_message(self, text):
        """发送消息到WebSocket"""
        #await asyncio.sleep(delay)
        if isinstance(text, str):
            message = Message(text)
            message.payload["params"]["group_id"] = self.group_id
            await self.websocket.send(json.dumps(message.payload))
        elif isinstance(text, Message):
            message = text
            if not message.has_group_id:
                message.payload["params"]["group_id"] = self.group_id
            await self.websocket.send(json.dumps(message.payload))

    async def send_poke(self, user_id):
        payload = {
                "action": "send_poke",
                "params": {
                    "user_id": user_id,
                    "group_id": self.group_id
                }
            }
        await self.send_message(Message(payload))

    async def send_emoji_like(self, message_id, emoji_id):
        payload = {
                    "action": "set_msg_emoji_like",
                    "params": {
                        "message_id": message_id,
                        "emoji_id": emoji_id
                    }
                }
        await self.send_message(Message(payload))

    async def send_message_list(self, send_list):
        """发送消息列表"""
        for send_item in send_list:
            await self.send_message(Message(send_item))

    def set_websocket(self, websocket):
        self.websocket = websocket

    async def process_message(self, data):
        """处理收到的消息"""

        if data.get("post_type") != "message" or data.get("message_type") != "group":
            return
        
        group_id = data["group_id"]
        if group_id not in self.config.target_groups:
            return
        

        self.self_id = str(data.get("self_id"))
        
        # 提取消息内容
        #text = "".join(seg["data"]["text"] for seg in data["message"] if seg["type"] == "text")
        user_id = data["user_id"]
        message_id = str(data.get("message_id"))
        nickname = data["sender"]["card"] or data["sender"]["nickname"]

        message = Message(user_id, message_id, nickname, data)
        data["message"]
        self.messages[str(message_id)] = message

        # 添加到历史记录
        self.llm_service.add_message_to_history(user_id, nickname, str(message))

        
        
        '''
        # 处理复读
        if await self.action_handler.handle_repeat(self, ws, group_id, raw_message):
            return
        
        # 处理关键词回复
        if await self.action_handler.handle_keyword_reply(self, ws, group_id, text):
            return
        
        # 处理特殊用户回复
        if await self.action_handler.handle_special_reply(self, ws, group_id, user_id, message_id, text):
            return
        
        # 处理贴表情
        await self.action_handler.handle_emoji(self, ws, user_id, message_id)
        
        # 处理随机艾特
        await self.action_handler.handle_random_at(self, ws, group_id, user_id, message_id)
        
        # 处理戳一戳
        await self.action_handler.handle_poke(self, ws, group_id, user_id)
        
        # 处理LLM回复
        if await self.action_handler.handle_llm_reply(
            self, ws, self.llm_service, group_id, message_id, user_id, nickname, text, raw_message
        ):
            return
        
        # 处理随机回复
        await self.action_handler.handle_random_reply(self, ws, group_id, text)'''

        # 事件广播
        await self.dispatch_event(EventType.EVENT_RECV_MSG, message)

        print(message)