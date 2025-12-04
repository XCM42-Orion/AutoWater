from message_utils import *
import random
from llm_service import *

class Module:
    def __init__(self):
        pass
    
class ModuleManager:
    def __init__(self):
        self.module_list = list()
        self.id_counter = 0

    def register_module(self, instance):
        self.id_counter += 1
        self.module_list.append(instance)
        return self.id_counter
    
class Repeat(Module):
    async def on_recv_msg(self, message_handler, message, config):
        """处理复读"""
        if str(message) == self.last_message:
            self.repeat_count += 1
            if random.random() <= config.repeat_possibility and self.repeat_count == 1:
                return await message_handler.send_message(Message(message))
        else:
            self.last_message = str(message)
            self.repeat_count = 0
        
        return False
    
    def register(self, message_handler):
        message_handler.register_listener(EventType.EVENT_RECV_MSG, self.on_recv_msg)
        self.last_message = ''
        self.repeat_count = 0

class RandomReply(Module):
    async def on_recv_msg(self, message_handler, message, config):
        """处理随机回复"""
        if not config.random_reply or random.random() > config.random_reply_possibility:
            return False
        
        reply_message = Message(random.choice(config.random_reply))
        
        await message_handler.send_message(reply_message)
        return True
    
    def register(self, message_handler):
        message_handler.register_listener(EventType.EVENT_RECV_MSG, self.on_recv_msg)


class AtReply(Module):
    async def on_recv_msg(self, message_handler, message, config):
        """处理随机回复"""
        # 检查是否被艾特
        data = message.data
        self_id = data.get("self_id")
        is_mentioned = False
        for component in message.get_components():
            if component.type == 'at' and component.data == self_id:
                is_mentioned = True
        # 处理被艾特回复
        if is_mentioned:
            if random.random() > config.ated_reply_possibility:
                return False
        
            if random.random() <= config.llm_possibility and config.llm_url:
                reply_lines = await message_handler.llm_service.call_llm(str(message), message.user_id, None)
                if reply_lines:
                    send_list = []
                    for idx, line in enumerate(reply_lines):
                        reply = ''
                        if idx == 0:
                            reply = [("reply",message.message_id),("at",message.user_id)," " + line.strip()]
                        else:
                            reply = [" " + line.strip()]
                        
                        send_list.append(Message(reply))
                    
                    await message_handler.send_message_list(send_list)
                    return True
            
            # 使用预定义的回复
            if config.ated_reply:
                await message_handler.send_message(Message(random.choice(config.ated_reply)))
                return True
            
            return False
        return True
    
    def register(self, message_handler):
        message_handler.register_listener(EventType.EVENT_RECV_MSG, self.on_recv_msg)

class Poke(Module):
    async def on_recv_msg(self, message_handler, message, config):
        """处理戳一戳"""
        if random.random() <= config.poke_possibility:
            await message_handler.send_poke(message.user_id)
            print("已戳一戳",message.user_id)
            return True
        return False
        
    def register(self, message_handler):
        message_handler.register_listener(EventType.EVENT_RECV_MSG, self.on_recv_msg)
##################



class KeywordReply(Module):
    async def on_recv_msg(self, message_handler, message, config):
        """处理关键词回复"""
        if not config.keyword_reply or random.random() > config.keyword_possibility:
            return False
        
        for keyword_item in config.keyword_reply:
            if keyword_item['keyword'] in str(message):
                await message_handler.send_message(Message(random.choice(keyword_item['reply'])))
                return True
        return False
    
    def register(self, message_handler):
        message_handler.register_listener(EventType.EVENT_RECV_MSG, self.on_recv_msg)

class SpecialReply(Module):
    async def on_recv_msg(self, message_handler, message, config):
        """处理特殊用户回复"""
        if not config.set_reply or random.random() > config.set_reply_possiblity:
            return False
        
        for special_user in config.set_reply:
            reply = ''
            if message.user_id == special_user['id']:
                reply = [('reply',message.message_id),special_user['reply']]
                await message_handler.send_message(Message(reply))
                return True
        return False
    
    def register(self, message_handler):
        message_handler.register_listener(EventType.EVENT_RECV_MSG, self.on_recv_msg)


class Emoji(Module):
    async def on_recv_msg(self, message_handler, message, config):
        """处理贴表情"""
        if not config.set_emoji or random.random() > config.emoji_possibility:
            return False
        
        for emoji_user in config.set_emoji:
            if message.user_id == emoji_user['id']:
                await message_handler.send_emoji_like(message.message_id,emoji_user['emoji_id'])
                return True
        return False
    
    def register(self, message_handler):
        message_handler.register_listener(EventType.EVENT_RECV_MSG, self.on_recv_msg)



class RandomAt(Module):
    async def on_recv_msg(self, message_handler, message, config):
        """处理随机艾特"""
        reply = ''
        if random.random() <= config.at_possibility:
            reply = [("reply",message.message_id),("at",message.user_id)]
            await message_handler.send_message(Message(reply))
            return True
        return False
    
    def register(self, message_handler):
        message_handler.register_listener(EventType.EVENT_RECV_MSG, self.on_recv_msg)


from heartflow import HeartFlow

class LLMReply(Module):
    async def on_recv_msg(self, message_handler, message, config):
        reply_lines = []
        if config.heartflow_do_heartflow:
            heartflow = HeartFlow(config)
            do_llm = await heartflow.should_reply(str(message), message.user_id, message.nickname)
            if not do_llm:
                return False
            else:
                reply_lines = await message_handler.llm_service.call_llm(str(message), message.user_id, message.nickname)
        else:
            if random.random() <= config.llm_possibility:
                reply_lines = await message_handler.llm_service.call_llm(str(message), message.user_id, message.nickname)
        
        if not reply_lines:
                return False
            
        send_list = []
        reply = ''
        for idx, line in enumerate(reply_lines):
            if idx == 0:
                reply = [('reply',message.message_id),('at',str(message.user_id))," " + line.strip()]
            else:
                reply = [line.strip()]
            send_list.append(Message(reply))
        await message_handler.send_message_list(send_list)
        return True
    def register(self, message_handler):
        message_handler.register_listener(EventType.EVENT_RECV_MSG, self.on_recv_msg)