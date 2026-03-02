from module import *
from message_utils import *
from event import *

class message_formatter(Module):
    prerequisite = ['archive']

    def register(self, message_handler, event_handler, mod):
        message_handler.register_listener(self, EventType.EVENT_INIT, self.on_init, -30)

    def __init__(self):
        pass
    
    async def on_init(self, event, context):
        message_handler = context.message_handler
        MessageComponent.__str__ = EventType.register_callable_hook_event('EVENT_MESSAGE_FORMAT',self,MessageComponent.__str__,context.event_handler)
        message_handler.register_listener(self, EventType.message_formatter.EVENT_MESSAGE_FORMAT, self.format, 100)


    #此处进行了hook，给str(Message)提供高级服务
    async def format(self, event, context):
        ret = ""
        archive = context.mod.archive
        vllm = None
        if context.mod.has_module('vision_llm') and context.mod.vision_llm.deployed:
            vllm = context.mod.vision_llm
        component = event.data.args[0]
        event.data.bypass_calling = True
        if component.type == 'reply':
            if not (archive.chat_history_manager.find_message_by_message_id(component.data) is None):
                ret = '[回复 ' + str(archive.chat_history_manager.find_message_by_message_id(component.data)) + ']'   #data->message_id
            else:
                ret = '[回复 ' + '某条消息' + ']'
        elif component.type == 'image':
            ret = '[图片]'
            if vllm != None:
                ret = f'[图片: {await vllm.call_vllm(component.data)}]'
        elif component.type == 'text':                 #data->str
            ret = component.data
        elif component.type == 'at':                   #data->qq_id
            at_name = str(component.data)
            person = archive.person_manager.find_person_by_qqid(int(component.data))
            if not person.unknown:
                at_name = person.nickname
            ret = '[@' + at_name + ']'

        event.data.ret.append(ret)

    