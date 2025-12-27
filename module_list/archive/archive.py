from module import *
from archive_utils import *
from event import *
from message_utils import *

from archive_events import *

class archive(Module):
    prerequisite = ['config', 'storage']

    def __init__(self):
        self.person_manager = PersonManager()
        self.chat_history_manager = ChatHistoryManager()

    async def update(self, event, context):
        message = event.data
        config = context.mod.config
        message_handler = context.message_handler        

        if message.user_id:
            if not (self.person_manager.find_person_by_qqid(message.user_id).unknown): 
                self.person_manager.update_nickname(message.user_id, message.nickname)
            else:
                self.person_manager.add_person(Person(message.user_id, message.nickname))

        if message.message_id:
            self.chat_history_manager.add_message(ChatHistory(message, 
                                                              self.person_manager.find_person_by_qqid(message.user_id)))
            
        event = Event(EventType.archive.EVENT_ARCHIVE_UPDATED, (self.person_manager, self.chat_history_manager,
                                            message))
        await context.event_handler.dispatch_custom_event(event, self)
        


    def register(self, message_handler, event_handler, mod):
        self.person_manager = mod.storage.permanent(self.person_manager, self, "person_manager")
        self.chat_history_manager = mod.storage.permanent(self.chat_history_manager, self, "chat_history_manager")
        message_handler.register_listener(self, EventType.EVENT_RECV_MSG, self.update, 1001)
        