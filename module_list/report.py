import asyncio
from datetime import datetime,time
from module import Module
from message_utils import *
from logger import Logger

class ReportService(Module):
    prerequisite = ['config']

    def __init__(self):
        pass
    
    def register(self,message_handler,event_handler,module_handler):
        message_handler.register_listener(self, EventType.EVENT_INIT, self.run)
        module_handler.config.register_config('time_reply', module=self)
        module_handler.config.register_config('do_report', module=self)


    async def run(self, event, context):
        self.config = context.mod.config
        """运行自动播报"""
        if not self.config.do_report or not self.config.time_reply:
            return False
        
        while True:
            now_time = datetime.now()
            for time_data in self.config.time_reply:
                reply_time = time.fromisoformat(time_data.get('time'))
                if reply_time.hour == now_time.hour and reply_time.minute == now_time.minute:
                    Logger().info(f"执行定时播报: {time_data.get('time')}，内容: {time_data.get('reply')}")
                    for group_id in self.config.target_groups:
                        await context.message_handler.send_message(Message(time_data.get('reply')),group_id)
            await asyncio.sleep(60)