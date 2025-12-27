from module import *

sys.path.append("..")

from archive.archive_utils import *
from event import *
from message_utils import *
from embedding_utils import *

from archive.archive_events import *

from event import *

class embedding(Module):
    prerequisite = ['config', 'storage', 'archive']

    def __init__(self):
        self.vector_manager = VectorizedChatHistoryManager()

        self.indices = None
    
    async def llm_call_wrapper(self, event, context):
        prompt_annotation = ''
        for indice in self.indices[1:]:
            messages = context.mod.archive.chat_history_manager.find_around(self.vector_manager.message_ids[indice], 10)
            if messages is None:
                continue
            for each in messages:
                prompt_annotation += str(each) + '\n'

            prompt_annotation += '-----------对话段分割线-----------\n'

        event.data.kwargs['prompt_annotation'] = prompt_annotation
            


    async def update(self, event, context):
        person_manager, chat_history_manager,\
            message = event.data

        str_message = str(message)
        config = context.mod.config
        message_handler = context.message_handler

        if str_message is None or str_message.strip() == '':
            return

        vector = self.vector_manager.add_sentence(str_message, message.message_id)

        similarity_vector = self.vector_manager.calc_similarity(vector)

        try:
            self.indices, top_k_values = self.vector_manager.top_k_similarity(similarity_vector, 3)
        except:
            return
        
        


        '''print(self.vector_manager.matrix.shape)
        
        print('最相似的10个句子')'''

    
        
    async def on_init(self, event, context):
        message_handler = context.message_handler
        context.mod.llm.call_llm = EventType.register_callable_hook_event('EVENT_LLM_HOOK',self,context.mod.llm.call_llm,context.event_handler)
        message_handler.register_listener(self, EventType.embedding.EVENT_LLM_HOOK, self.llm_call_wrapper, 50)

    def register(self, message_handler, event_handler, mod):
        self.vector_manager = mod.storage.permanent(self.vector_manager, self, "vector_manager")
        message_handler.register_listener(self, EventType.EVENT_INIT, self.on_init, 0)
        message_handler.register_listener(self, EventType.archive.EVENT_ARCHIVE_UPDATED, self.update, 0)
        