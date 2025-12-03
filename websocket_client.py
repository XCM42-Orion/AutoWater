import websockets
import asyncio
import json
from message_utils import MessageHandler
from report import ReportService
from module import *

class WebSocketClient:
    def __init__(self, config):
        self.config = config
        self.report_service = ReportService(config)
        self.message_handler = None

        #测试代码


    def module_init(self):
        repeat = Repeat()
        random_reply = RandomReply()
        at_reply = AtReply()
        poke = Poke()
        keyword_reply = KeywordReply()
        special_reply = SpecialReply()
        emoji = Emoji()
        random_at = RandomAt()
        llm_reply = LLMReply()
        

        repeat.register(self.message_handler)
        random_reply.register(self.message_handler)
        at_reply.register(self.message_handler)
        poke.register(self.message_handler)
        keyword_reply.register(self.message_handler)
        special_reply.register(self.message_handler)
        emoji.register(self.message_handler)
        random_at.register(self.message_handler)
        llm_reply.register(self.message_handler)
    
    async def connect(self):
        """连接WebSocket并处理消息"""
        async with websockets.connect(
            self.config.napcat_url,
            ping_interval=60,
            ping_timeout=30,
            close_timeout=10
        ) as ws:
            print("Napcat WebSocket 已连接")


            self.message_handler = MessageHandler(self.config, ws)
            self.module_init()



            # 并发运行消息处理和自动播报
            await asyncio.gather(
                self._handle_messages(ws),
                self.report_service.run(ws)
            )
    
    async def _handle_messages(self, ws):
        """处理WebSocket消息"""
        async for message in ws:
                data = json.loads(message)
                await self.message_handler.process_message(data)