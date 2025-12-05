import websockets
import asyncio
import json
from message_utils import MessageHandler
from report import ReportService
import module
import signal
from typing import *

class WebSocketClient:
    def __init__(self, url):
        #报时系统等待移植为module...
        #self.report_service = ReportService(config)
        self.url = url
        self.module_handler = module.ModuleHandler()
        self.message_handler = None

        signal.signal(signal.SIGINT, self.exit_handler) 
        signal.signal(signal.SIGTERM, self.exit_handler) 


    def exit_handler(self,signum, frame):
        self.module_handler.unload_all()
        exit(0)


    def module_init(self):
        # 获取所有模块
        module_dict = module.scan_module()
        self.module_handler.load_module(module_dict, self.message_handler)


        '''repeat = Repeat()
        random_reply = RandomReply()
        at_reply = AtReply()
        poke = Poke()
        keyword_reply = KeywordReply()
        special_reply = SpecialReply()
        emoji = Emoji()
        random_at = RandomAt()
        llm_reply = LLMReply()
        follow_emoji = FollowEmoji(emoji_replied=self.emoji_replied)
        emoji_threshold = EmojiThreshold(emoji_counted_message=self.emoji_counted_message)
        

        repeat.register(self.message_handler)
        random_reply.register(self.message_handler)
        at_reply.register(self.message_handler)
        poke.register(self.message_handler)
        keyword_reply.register(self.message_handler)
        special_reply.register(self.message_handler)
        emoji.register(self.message_handler)
        random_at.register(self.message_handler)
        llm_reply.register(self.message_handler)
        follow_emoji.register(self.message_handler)
        emoji_threshold.register(self.message_handler)'''
    
    async def connect(self):
        """连接WebSocket并处理消息"""
        async with websockets.connect(
            self.url,
            ping_interval=60,
            ping_timeout=30,
            close_timeout=10
        ) as ws:
            print("Napcat WebSocket 已连接")


            self.message_handler = MessageHandler(ws, self.module_handler)
            self.module_init()
            self.message_handler.start_message_handler()


            # 并发运行消息处理和自动播报
            await asyncio.gather(
                self._handle_messages(ws)
            )#                self.report_service.run(ws)
    
    async def _handle_messages(self, ws):
        """处理WebSocket消息"""
        async for message in ws:
                data = json.loads(message)
                await self.message_handler.process_message(data)