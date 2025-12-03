import json
from actions import ActionHandler
from llm_service import LLMService

class MessageHandler:
    def __init__(self, config):
        self.config = config
        self.action_handler = ActionHandler(config)
        self.llm_service = LLMService(config)

    
    async def process_message(self, ws, data):
        """处理收到的消息"""
        if data.get("post_type") != "message" or data.get("message_type") != "group":
            return
        
        group_id = data["group_id"]
        if group_id not in self.config.target_groups:
            return
        
        # 提取消息内容
        text = "".join(seg["data"]["text"] for seg in data["message"] if seg["type"] == "text")
        raw_message = data.get("raw_message", "")
        user_id = data["user_id"]
        message_id = data.get("message_id")
        nickname = data["sender"]["card"] or data["sender"]["nickname"]
        
        # 添加到历史记录
        self.llm_service.add_message_to_history(user_id, nickname, text)
        
        # 检查是否被艾特
        self_id = str(data.get("self_id"))
        is_mentioned = any(
            seg.get("type") == "at" and seg["data"].get("qq") == self_id 
            for seg in data.get("message", [])
        )
        
        # 处理被艾特回复
        if is_mentioned:
            await self.action_handler.handle_mentioned_reply(
                ws, self.llm_service, group_id, message_id, user_id, raw_message, text
            )
            return
        
        # 处理复读
        if await self.action_handler.handle_repeat(ws, group_id, raw_message):
            return
        
        # 处理关键词回复
        if await self.action_handler.handle_keyword_reply(ws, group_id, text):
            return
        
        # 处理特殊用户回复
        if await self.action_handler.handle_special_reply(ws, group_id, user_id, message_id, text):
            return
        
        # 处理贴表情
        await self.action_handler.handle_emoji(ws, user_id, message_id)
        
        # 处理随机艾特
        await self.action_handler.handle_random_at(ws, group_id, user_id, message_id)
        
        # 处理戳一戳
        await self.action_handler.handle_poke(ws, group_id, user_id)
        
        # 处理LLM回复
        if await self.action_handler.handle_llm_reply(
            ws, self.llm_service, group_id, message_id, user_id, nickname, text, raw_message
        ):
            return
        
        # 处理随机回复
        await self.action_handler.handle_random_reply(ws, group_id, text)