import aiohttp
from collections import deque
from datetime import datetime
from module import *

class llm(Module):
    prerequisite = ['config']


    def __init__(self):
        self.config = None
        self.recent_messages = None

    def register(self, message_handler, event_handler, mod):
        self.config = mod.config
        self.recent_messages = deque(maxlen=self.config.background_message_number)
    
    def add_message_to_history(self, user_id, sender, text):
        """添加消息到历史记录"""
        self.recent_messages.append({
            "user_id": user_id,
            "sender": sender,
            "time": datetime.now().isoformat(),
            "text": text
        })
    
    async def call_llm(self, user_msg, user_id=None, nickname=None):
        """调用LLM API"""
        messages = []
        messages.append({
            "role": "system",
            "content": self.config.llm_prompt
        })
        
        # 添加上下文消息
        if self.recent_messages:
            for msg in self.recent_messages:
                display_name = f"{msg['sender']}({msg['user_id']})"
                messages.append({
                    "role": "user",
                    "content": f"{display_name}: {msg['text']}"
                })
        
        # 当前用户消息
        if user_id and nickname:
            display_name = f"{nickname}({user_id})"
            messages.append({"role": "user", "content": f"{display_name}: {user_msg}"})
        else:
            messages.append({"role": "user", "content": user_msg})
        
        payload = {
            "model": self.config.llm_model,
            "messages": messages,
            "stream": False,
            "temperature": self.config.llm_temperature,
            "max_tokens": self.config.llm_max_tokens
        }
        
        headers = {
            "Authorization": f"Bearer {self.config.llm_apikey}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.config.llm_url, headers=headers, json=payload) as resp:
                    resp.raise_for_status()
                    result = await resp.json()
                    raw_str = result["choices"][0]["message"]["content"]
                    print(f"LLM返回原始内容: {raw_str}")
                    return raw_str.split('%n')
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return []
        
    async def on_recv_msg(self, event, context):
        message = event.data
        config = context.mod.config
        message_handler = context.message_handler

        self.add_message_to_history(message.user_id, message.nickname, str(message))