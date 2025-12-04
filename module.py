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

    def register_module(self, instance:Module):
        self.id_counter += 1
        self.module_list.append(instance)
        return self.id_counter
    