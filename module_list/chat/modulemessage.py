from message_utils import *
import random
from module import Module
from logger import Logger

class MessageModule(Module):
    prerequisite = ['config']
    def __init__(self):
        pass
    async def on_recv_msg(self, event : Event, context : EventContext):
        pass
    def register(self, message_handler, event_handler, module_handler):
        message_handler.register_listener(self, EventType.EVENT_RECV_MSG, self.on_recv_msg)


class Repeat(MessageModule):
    async def on_recv_msg(self, event, context):
        """处理复读"""
        message = event.data
        config = context.mod.config
        message_handler = context.message_handler

        if str(message) == self.last_message:
            self.repeat_count += 1
            if random.random() <= config.repeat_possibility and self.repeat_count == 1:
                logger = Logger()
                logger.info(f"触发复读：{message}")
                return await message_handler.send_message(Message(message),message.data.get('group_id'))
        else:
            self.last_message = str(message)
            self.repeat_count = 0
        
        return False
    
    def register(self, message_handler, event_handler, module_handler):
        module_handler.config.register_config('repeat_possibility', module=self)

        self.last_message = ''
        self.repeat_count = 0
        super().register(message_handler, event_handler, module_handler)

class RandomReply(MessageModule):
    async def on_recv_msg(self, event, context):
        """处理随机回复"""
        message = event.data
        config = context.mod.config
        message_handler = context.message_handler


        if not config.random_reply or random.random() > config.random_reply_possibility:
            return False
        
        reply_message = Message(random.choice(config.random_reply))
        logger = Logger()
        logger.info(f"触发随机回复：{reply_message}")
        return await message_handler.send_message(reply_message,message.data.get('group_id'))
    

    def register(self, message_handler, event_handler, module_handler):
        module_handler.config.register_config('random_reply', module=self)
        module_handler.config.register_config('random_reply_possibility', module=self)

        super().register(message_handler, event_handler, module_handler)
    


class AtReply(MessageModule):
    async def on_recv_msg(self, event, context):
        """处理随机回复"""
        message = event.data
        config = context.mod.config
        message_handler = context.message_handler


        # 检查是否被艾特
        data = message.data
        self_id = data.get("self_id")
        group_id = data.get("group_id")
        is_mentioned = False
        for component in message.get_components():
            if component.type == 'at' and component.data == self_id:
                is_mentioned = True
        # 处理被艾特回复
        if is_mentioned:
            if random.random() > config.ated_reply_possibility:
                return False
        
            if random.random() <= config.llm_possibility and config.llm_url:
                logger = Logger()
                logger.info("触发被艾特LLM回复，开始调用LLM接口")
                reply_lines = await context.mod.llm.call_llm()
                logger.info(f"触发被艾特LLM回复：{reply_lines}")
                if reply_lines:
                    send_list = []
                    for idx, line in enumerate(reply_lines):
                        reply = ''
                        if idx == 0:
                            reply = [("reply",message.message_id),("at",message.user_id)," " + line.strip()]
                        else:
                            reply = [" " + line.strip()]
                        
                        send_list.append(Message(reply))
                    
                    return await message_handler.send_message(send_list,group_id)
            
            # 使用预定义的回复
            if config.ated_reply:
                logger = Logger()
                logger.info(f"触发被艾特预定义回复：{config.ated_reply}")
                return await message_handler.send_message(Message(random.choice(config.ated_reply)),group_id)
            
            return False
        return False
    def register(self, message_handler, event_handler, module_handler):
        module_handler.config.register_config('ated_reply_possibility', module=self)
        module_handler.config.register_config('ated_reply', module=self)
        module_handler.config.register_config('llm_possibility', module=self)
        super().register(message_handler, event_handler, module_handler)
    

class Poke(MessageModule):
    async def on_recv_msg(self, event, context):
        """处理戳一戳"""
        message = event.data
        config = context.mod.config
        message_handler = context.message_handler


        if random.random() <= config.poke_possibility:
            return await message_handler.send_poke(message.user_id)
        return False
    
    def register(self, message_handler, event_handler, module_handler):
        module_handler.config.register_config('poke_possibility', module=self)
        super().register(message_handler, event_handler, module_handler)
        
##################



class KeywordReply(MessageModule):
    async def on_recv_msg(self, event, context):
        """处理关键词回复"""
        message = event.data
        config = context.mod.config
        message_handler = context.message_handler


        if not config.keyword_reply or random.random() > config.keyword_possibility:
            return False
        
        for keyword_item in config.keyword_reply:
            if keyword_item['keyword'] in str(message):
                logger = Logger()
                logger.info(f"触发关键词回复：{keyword_item['keyword']} -> {keyword_item['reply']}")
                return message_handler.send_message(Message(random.choice(keyword_item['reply']),message.data.get('group_id')))
        return False
    
    def register(self, message_handler, event_handler, module_handler):
        module_handler.config.register_config('keyword_reply', module=self)
        module_handler.config.register_config('keyword_possibility', module=self)
        super().register(message_handler, event_handler, module_handler)
    

class SpecialReply(MessageModule):
    async def on_recv_msg(self, event, context):
        """处理特殊用户回复"""
        message = event.data
        config = context.mod.config
        message_handler = context.message_handler



        if not config.set_reply or random.random() > config.set_reply_possibility:
            return False
        
        for special_user in config.set_reply:
            reply = ''
            if message.user_id == special_user['id']:
                reply = [('reply',message.message_id),special_user['reply']]
                logger = Logger()
                logger.info(f"触发特殊用户回复：{special_user['id']} -> {special_user['reply']}")
                return await message_handler.send_message(Message(reply),message.data.get('group_id'))
        return False
    
    
    def register(self, message_handler, event_handler, module_handler):
        module_handler.config.register_config('set_reply', module=self)
        module_handler.config.register_config('set_reply_possibility', module=self)
        super().register(message_handler, event_handler, module_handler)
    


class Emoji(MessageModule):
    async def on_recv_msg(self, event, context):
        """处理贴表情"""
        message = event.data
        config = context.mod.config
        message_handler = context.message_handler


        if not config.set_emoji or random.random() > config.emoji_possibility:
            return False
        
        for emoji_user in config.set_emoji:
            if message.user_id == emoji_user['id']:
                return await message_handler.send_emoji_like(message.message_id,emoji_user['emoji_id'])
        return False
    
    def register(self, message_handler, event_handler, module_handler):
        module_handler.config.register_config('set_emoji', module=self)
        module_handler.config.register_config('emoji_possibility', module=self)
        super().register(message_handler, event_handler, module_handler)
    



class RandomAt(MessageModule):
    async def on_recv_msg(self, event, context):
        """处理随机艾特"""
        message = event.data
        config = context.mod.config
        message_handler = context.message_handler


        reply = ''
        if random.random() <= config.at_possibility:
            reply = [("reply",message.message_id),("at",message.user_id)]
            logger = Logger()
            logger.info(f"触发随机艾特：@{message.user_id}")
            return await message_handler.send_message(Message(reply),message.data.get('group_id'))
        return False
    
    def register(self, message_handler, event_handler, module_handler):
        module_handler.config.register_config('at_possibility', module=self)
        super().register(message_handler, event_handler, module_handler)
    

class LLMReply(MessageModule):
    async def on_recv_msg(self, event, context):
        reply_lines = []
        message = event.data
        config = context.mod.config
        message_handler = context.message_handler


        if config.heartflow_do_heartflow:
            do_llm = await context.mod.heartflow.should_reply(str(message), message.user_id, message.nickname)
            if not do_llm:
                return False
            else:
                reply_lines = await context.mod.llm.call_llm()
        else:
            if random.random() <= config.llm_possibility:
                reply_lines = await context.mod.llm.call_llm()
        
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
        return await message_handler.send_message(send_list)
    
    def register(self, message_handler, event_handler, module_handler):
        module_handler.config.register_config('llm_possibility', module=self)
        module_handler.config.register_config('heartflow_do_heartflow','heartflow_settings.do_heartflow', module=self)
        super().register(message_handler, event_handler, 
                         module_handler)
