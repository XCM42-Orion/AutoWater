import websockets
import asyncio
import json
from message_utils import MessageHandler, EventType
import module
import signal
from typing import *
from logger import Logger

class WebSocketClient:
    def __init__(self, url):

        self.url = url
        self.module_handler = module.ModuleHandler()
        self.message_handler = None
        self.logger = Logger()
        signal.signal(signal.SIGINT, self.exit_handler) 
        signal.signal(signal.SIGTERM, self.exit_handler) 


    def exit_handler(self,signum, frame):
        self.module_handler.unload_all()
        exit(0)

    def module_init(self):
        # 获取所有模块
        module_dict = module.scan_module()
        self.module_handler.load_module(module_dict, self.message_handler)
    
    async def connect(self):
        """连接WebSocket并处理消息"""
        while True:
            try:
                async with websockets.connect(
                    self.url,
                    ping_interval=60,
                    ping_timeout=30,
                    close_timeout=10
                ) as ws:
                    self.logger.debug("Napcat WebSocket 已连接")

                    self.message_handler = MessageHandler(ws, self.module_handler)
                    self.module_init()
                    self.logger.debug("模块初始化完成")
                    self.message_handler.start_message_handler()
                    self.logger.debug("消息处理器已启动")
                    asyncio.create_task(self.message_handler.dispatch_event(EventType.EVENT_INIT, None))
                    self.logger.debug("Autowater 启动完成。")
                    # 运行消息处理
                    await self._handle_messages(ws)
                    break
            except Exception as e:
                self.logger.error(f"WebSocket连接错误: {e}，正在尝试重新连接...")
                await asyncio.sleep(5)
                continue
    
    async def _handle_messages(self, ws):
        """处理WebSocket消息"""
        async for message in ws:
                data = json.loads(message)
                asyncio.create_task(self.message_handler.process_message(data))
