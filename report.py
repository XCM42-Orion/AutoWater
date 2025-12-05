import json
import asyncio
from datetime import datetime, time

class ReportService:
    def __init__(self, config):
        self.config = config
    
    async def run(self, ws):
        """运行自动播报"""
        if not self.config.do_report or not self.config.time_reply:
            return
        
        while True:
            now_time = datetime.now()
            for time_data in self.config.time_reply:
                reply_time = time.fromisoformat(time_data.get('time'))
                if reply_time.hour == now_time.hour and reply_time.minute == now_time.minute:
                    for group_id in self.config.target_groups:
                        payload = {
                            "action": "send_group_msg",
                            "params": {
                                "group_id": group_id,
                                "message": time_data.get('reply')
                            }
                        }
                        await ws.send(json.dumps(payload))
            await asyncio.sleep(60)