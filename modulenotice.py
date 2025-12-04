from message_utils import *
import random
from llm_service import *
from module import Module

class NoticeModule(Module):
    def __init__(self):
        pass
    async def on_notice_msg(self, message_handler, message, config):
        pass
    def register(self, message_handler):
        message_handler.register_listener(EventType.EVENT_NOTICE_MSG, self.on_notice_msg)


class FollowEmoji(NoticeModule):
    def __init__(self,emoji_replied):
        self.emoji_replied = emoji_replied

    async def on_notice_msg(self,message_handler,message,config):
        """处理跟随贴表情"""
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
                    await message_handler.send_emoji_like(message_id,emoji_id)
                    print(f"已为消息{message_id}贴表情{emoji_id}")
                    return True
        return False
    

class EmojiThreshold(NoticeModule):
    def __init__(self,emoji_counted_message):
        self.emoji_counted_message = emoji_counted_message


    async def on_notice_msg(self,message_handler,message,config):
        """处理表情达标回复"""
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
                            await message_handler.send_message(Message(finalreply),message.data.get('group_id'))
                            print(f"消息{message_id}表情{emoji_id}达标，已回复{finalreply}")
                            return True
        return False
