from message_utils import *
import random
from history import *
from module import Module
from event import *
from logger import Logger

class NoticeModule(Module):
    prerequisite = ['config','historyhandler']
    def __init__(self):
        pass
    async def on_notice_msg(self, event : Event, event_handler : EventHandler):
        pass


class FollowEmoji(NoticeModule):
    def __init__(self):
        # 已回复过的emoji 消息
        self.emoji_replied = None

    def register(self, message_handler, event_handler, mod):
        self.emoji_replied = mod.historyhandler.HistoryHandler(cache_path='data/emoji_replied')
        self.emoji_replied.load()

        config = mod.config

        config.register_config('follow_emoji', 'do_follow_emoji', module=self)
        config.register_config('follow_emoji_possibility', module=self)

        message_handler.register_listener(self, EventType.EVENT_NOTICE_MSG, self.on_notice_msg)

    async def on_notice_msg(self, event, event_context):
        """处理跟随贴表情"""
        message = event.data
        config = event_context.mod.config
        message_handler = event_context.message_handler


        if (not config.follow_emoji) or (random.random() > config.follow_emoji_possibility):
            return False
        
        data = message.data

        if data.get("notice_type") != "group_msg_emoji_like":
            return False
        if not data.get("is_add"):
            return False
        
        message_id = data.get("message_id")
        emoji_data = data.get("likes",[])

        for emoji in emoji_data:
            emoji_id = emoji.get("emoji_id")
            if random.random() <= config.follow_emoji_possibility:
                if not self.emoji_replied.query((message_id,emoji_id)):
                    self.emoji_replied.insert((message_id,emoji_id))
                    return await message_handler.send_emoji_like(message_id, emoji_id)
        return False
    def unregister(self):
        self.emoji_replied.dump()
    

class EmojiThreshold(NoticeModule):
    def __init__(self):
        # 已达到消息阈值的emoji 消息
        self.emoji_counted_message = None
        self.logger = Logger()


    async def on_notice_msg(self, event, event_context):
        """处理表情达标回复"""
        message = event.data
        config = event_context.mod.config
        message_handler = event_context.message_handler


        if not config.do_emoji_threshold_reply:
            return False
        
        data = message.data
        if data.get("notice_type") != "group_msg_emoji_like":
            return False
        
        group_id = data.get("group_id")
        message_id = data.get("message_id")
        emoji_data = data.get("likes",[])


        for emoji in emoji_data:
            emoji_id = emoji.get("emoji_id")
            emoji_count = emoji.get('count')
            for reply in config.emoji_threshold_reply:
                if int(reply.get('emoji_id')) == int(emoji_id) and int(reply.get('count')) <= int(emoji_count):
                    if not self.emoji_counted_message.query((message_id,emoji_id)):
                        if random.random() <= config.emoji_threshold_reply_possibility:
                            self.emoji_counted_message.insert((message_id,emoji_id))
                            finalreply = random.choice(reply.get('reply'))
                            self.logger.info(f"消息{message_id}表情{emoji_id}达标")
                            return await message_handler.send_message(Message(finalreply),message.data.get('group_id'))
        return False
    
    def register(self, message_handler, event_handler, mod):
        self.emoji_counted_message = mod.historyhandler.HistoryHandler(cache_path='data/emoji_message')
        self.emoji_counted_message.load()

        config = mod.config

        config.register_config('emoji_threshold_reply', module=self)
        config.register_config('emoji_threshold_reply_possibility', module=self)
        config.register_config('do_emoji_threshold_reply', module=self)

        message_handler.register_listener(self, EventType.EVENT_NOTICE_MSG, self.on_notice_msg)

    def unregister(self):
        self.emoji_counted_message.dump()
