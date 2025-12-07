from collections import deque
import aiohttp
import json
import random
from module import *
import config
import logger

class heartflow(Module):
    prerequisite = ['llm','config']
    def __init__(self):
        self.config = None
        self.recent_messages = None
        self.logger = logger.Logger()

    def register(self, message_handler, event_handler, mod):
        self.config = mod.config
        self.recent_messages = deque(maxlen=self.config.heartflow_background_message_number)
    
    def add_message_to_history(self, user_id, sender, text):
        """添加消息到历史记录"""
        self.recent_messages.append({
            "user_id": user_id,
            "sender": sender,
            "text": text
        })
    
    async def call_heartflow_llm(self, user_msg, user_id=None, nickname=None):
        """调用 HeartFlow API"""
        messages = []
        messages.append({
            "role": "system",
            "content":f"现在你是{nickname}({user_id})，你的人格设定如下：{self.config.llm_prompt}。\n 请根据以下的聊天记录判断你现在要不要回复。你将根据最新的一条用户消息，输出两个用于决定是否回复的数值参数。所有输出必须是 JSON 格式，不得包含解释或其他文本。\n请根据用户消息判断：\n1. social_willingness：机器人当前对该消息的社交意愿度，范围 0~1。\n   - 内容与你相关、提到你、@你、像是跟你说话 → 值更高。\n   - 内容轻松、日常、生活话题 → 稍高。\n   - 内容无关、低价值、刷屏、重复 → 较低。\n   - 内容与专业或严肃知识相关（除非是你感兴趣的话题） → 较低（因为机器人不想正经回答）。\n   - 完全看不懂或无意义 → 非常低。\n2. context_weight：上下文相关性权重，范围 0~1。\n   - 查看上下文是否与你有关。\n  - 如果消息与你无关可以更低，与你相关性高可以更高。 \n 请直接输出如下 JSON（必须严格符合此格式，不能有任何额外内容）：\n{{\n  \"social_willingness\": 0.x,\n  \"context_weight\": 0.x\n}}\n务必确保两个数都是 0~1 的小数。"
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
            "model": self.config.heartflow_model,
            "messages": messages,
            "temperature": self.config.heartflow_temperature,
            "willing_weight": self.config.heartflow_willing_weight,
            "context_weight": self.config.heartflow_context_weight,
            "random_weight": self.config.heartflow_random_weight,
            "reply_threshold": self.config.heartflow_reply_threshold
        }
        
        headers = {
            "Authorization": f"Bearer {self.config.heartflow_api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.config.heartflow_api_url, headers=headers, json=payload) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            self.logger.error(f"HeartFlow API 调用出错: {e}")
            return ""
        
    async def should_reply(self, user_msg, user_id=None, nickname=None):
        """判断是否回复"""
        response = await self.call_heartflow_llm(user_msg, user_id, nickname)
        self.logger.info(f"HeartFlow API 返回: {response}")
        result = json.loads(response)
        social_willingness = float(result.get("social_willingness", 0))
        context_weight = float(result.get("context_weight", 0))
        reply_willingness = social_willingness*self.config.heartflow_willing_weight + context_weight*self.config.heartflow_context_weight + self.config.heartflow_random_weight*random.random()
        self.logger.info(f"HeartFlow 计算的回复意愿值: {reply_willingness}")
        if reply_willingness >= self.config.heartflow_reply_threshold:
                return True
        else:
                return False