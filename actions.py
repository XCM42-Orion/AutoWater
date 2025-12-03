'''import random
from utils import calculate_send_delay
from heartflow import HeartFlow

class ActionHandler:
    def __init__(self, config):
        self.config = config
        self.last_message = ''
        self.repeat_count = 0
    
    async def handle_repeat(self, message_handler, ws, group_id, text):
        """处理复读"""
        if text == self.last_message:
            self.repeat_count += 1
            if random.random() <= self.config.repeat_possibility and self.repeat_count == 1:
                payload = {
                    "action": "send_group_msg",
                    "params": {
                        "group_id": group_id,
                        "message": text
                    }
                }
                return await message_handler.send_message(ws, 0.2, payload)
        else:
            self.last_message = text
            self.repeat_count = 0
        return False
    
    async def handle_keyword_reply(self, message_handler, ws, group_id, text):
        """处理关键词回复"""
        if not self.config.keyword_reply or random.random() > self.config.keyword_possibility:
            return False
        
        for keyword_item in self.config.keyword_reply:
            if keyword_item['keyword'] in text:
                reply = random.choice(keyword_item['reply'])
                payload = {
                    "action": "send_group_msg",
                    "params": {
                        "group_id": group_id,
                        "message": reply
                    }
                }
                delay = calculate_send_delay(text, reply)
                await message_handler.send_message(ws, delay, payload)
                return True
        return False
    
    async def handle_special_reply(self, message_handler, ws, group_id, user_id, message_id, text):
        """处理特殊用户回复"""
        if not self.config.set_reply or random.random() > self.config.set_reply_possiblity:
            return False
        
        for special_user in self.config.set_reply:
            if user_id == special_user['id']:
                payload = {
                    "action": "send_group_msg",
                    "params": {
                        "group_id": group_id,
                        "message": [
                            {
                                "type": "reply",
                                "data": {"id": message_id}
                            },
                            {
                                "type": "text",
                                "data": {"text": special_user['reply']}
                            }
                        ]
                    }
                }
                delay = calculate_send_delay(text, special_user['reply'])
                await message_handler.send_message(ws, delay, payload)
                return True
        return False
    
    async def handle_emoji(self, message_handler, ws, user_id, message_id):
        """处理贴表情"""
        if not self.config.set_emoji or random.random() > self.config.emoji_possibility:
            return False
        
        for emoji_user in self.config.set_emoji:
            if user_id == emoji_user['id']:
                payload = {
                    "action": "set_msg_emoji_like",
                    "params": {
                        "message_id": message_id,
                        "emoji_id": emoji_user['emoji_id']
                    }
                }
                await message_handler.send_message(ws, 3, payload)
                return True
        return False
    
    async def handle_random_at(self, message_handler, ws, group_id, user_id, message_id):
        """处理随机艾特"""
        if random.random() <= self.config.at_possibility:
            payload = {
                "action": "send_group_msg",
                "params": {
                    "group_id": group_id,
                    "message": [
                        {
                            "type": "reply",
                            "data": {"id": message_id}
                        },
                        {
                            "type": "at",
                            "data": {"qq": str(user_id)}
                        }
                    ]
                }
            }
            await message_handler.send_message(ws, 3, payload)
            return True
        return False
    
    async def handle_poke(self, message_handler, ws, group_id, user_id):
        """处理戳一戳"""
        if random.random() <= self.config.poke_possibility:
            payload = {
                "action": "send_poke",
                "params": {
                    "user_id": user_id,
                    "group_id": group_id
                }
            }
            await message_handler.send_message(ws, 3, payload)
            return True
        return False
    
    async def handle_llm_reply(self, message_handler, ws, llm_service, group_id, message_id, user_id, nickname, text, raw_message):
        """处理LLM回复"""
        reply_lines = []
        if self.config.heartflow_do_heartflow:
            heartflow = HeartFlow(self.config)
            do_llm = await heartflow.should_reply(raw_message or text, user_id, nickname)
            if not do_llm:
                return False
            else:
                reply_lines = await llm_service.call_llm(raw_message or text, user_id, nickname)
        else:
            if random.random() <= self.config.llm_possibility:
                reply_lines = await llm_service.call_llm(raw_message or text, user_id, nickname)
        
        if not reply_lines:
                return False
            
        send_list = []
        for idx, line in enumerate(reply_lines):
            if idx == 0:
                    payload = {
                        "action": "send_group_msg",
                        "params": {
                            "group_id": group_id,
                            "message": [
                                {
                                    "type": "reply",
                                    "data": {"id": message_id}
                                },
                                {
                                    "type": "at",
                                    "data": {"qq": str(user_id)}
                                },
                                {
                                    "type": "text",
                                    "data": {"text": " " + line.strip()}
                                }
                            ]
                        }
                    }
                    delay = calculate_send_delay(text, line)
            else:
                    payload = {
                        "action": "send_group_msg",
                        "params": {
                            "group_id": group_id,
                            "message": line.strip()
                        }
                    }
                    delay = len(line) * 0.3
                
            send_list.append({"delay": delay, "payload": payload})
            
        await message_handler.send_message_list(ws, send_list)
        return True
    
    async def handle_random_reply(self, message_handler, ws, group_id, text):
        """处理随机回复"""
        if not self.config.random_reply or random.random() > self.config.random_reply_possibility:
            return False
        
        reply = random.choice(self.config.random_reply)
        payload = {
            "action": "send_group_msg",
            "params": {
                "group_id": group_id,
                "message": reply
            }
        }
        delay = calculate_send_delay(text, reply)
        await message_handler.send_message(ws, delay, payload)
        return True
    
    async def handle_mentioned_reply(self, message_handler, ws, llm_service, group_id, message_id, user_id, raw_message, text):
        """处理被艾特回复"""
        if random.random() > self.config.ated_reply_possibility:
            return False
        
        if random.random() <= self.config.llm_possibility and self.config.llm_url:
            reply_lines = await llm_service.call_llm(raw_message or text, user_id, None)
            if reply_lines:
                send_list = []
                for idx, line in enumerate(reply_lines):
                    if idx == 0:
                        payload = {
                            "action": "send_group_msg",
                            "params": {
                                "group_id": group_id,
                                "message": [
                                    {
                                        "type": "reply",
                                        "data": {"id": message_id}
                                    },
                                    {
                                        "type": "at",
                                        "data": {"qq": str(user_id)}
                                    },
                                    {
                                        "type": "text",
                                        "data": {"text": " " + line.strip()}
                                    }
                                ]
                            }
                        }
                        delay = calculate_send_delay(text, line)
                    else:
                        payload = {
                            "action": "send_group_msg",
                            "params": {
                                "group_id": group_id,
                                "message": line.strip()
                            }
                        }
                        delay = len(line) * 0.3
                    
                    send_list.append({"delay": delay, "payload": payload})
                
                await message_handler.send_message_list(ws, send_list)
                return True
        
        # 使用预定义的回复
        if self.config.ated_reply:
            reply = random.choice(self.config.ated_reply)
            payload = {
                "action": "send_group_msg",
                "params": {
                    "group_id": group_id,
                    "message": reply
                }
            }
            delay = len(reply) * 0.3 + 1
            await message_handler.send_message(ws, delay, payload)
            return True
        
        return False'''

### deprecated!!