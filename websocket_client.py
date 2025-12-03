import websockets
import asyncio
import json
from message_handler import MessageHandler
from report import ReportService

class WebSocketClient:
    def __init__(self, config):
        self.config = config
        self.message_handler = MessageHandler(config)
        self.report_service = ReportService(config)
    
    async def connect(self):
        """连接WebSocket并处理消息"""
        async with websockets.connect(
            self.config.napcat_url,
            ping_interval=60,
            ping_timeout=30,
            close_timeout=10
        ) as ws:
            print("Napcat WebSocket 已连接")
            
            # 并发运行消息处理和自动播报
            await asyncio.gather(
                self._handle_messages(ws),
                self.report_service.run(ws)
            )
    
    async def _handle_messages(self, ws):
        """处理WebSocket消息"""
        async for message in ws:
                data = json.loads(message)
                await self.message_handler.process_message(ws, data)