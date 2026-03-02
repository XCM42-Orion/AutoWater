from collections import OrderedDict
from datetime import datetime
import json
from module import *

# -----------------------------
# 处理历史信息（By Catismfans）
# -----------------------------

class historyhandler(Module):
    class HistoryHandler:
        def __init__(self,cache_path,maximum_size=1000):
            
            self.data=OrderedDict()
            self.cache_path=cache_path
            self.maximum_size=maximum_size

        # dump history into 
        def dump(self):   
            try:
                with open(self.cache_path,'w') as f :
                    json.dump(self.data,f)
            except:
                pass

        def load(self):
            try:
                with open(self.cache_path,'r') as f :
                    self.data=json.load(f)
            except:
                self.data={}

        # clear oldest history to maximum_size if exceeds max_size
        def maintain_size(self):
            while len(self.data) > self.maximum_size:
                self.data.popitem(last=False)

        # insert element into self
        def insert(self, key, val=None):
            if val is None:
                val=int(datetime.now().timestamp())
            self.data[str(key)]=val
            self.maintain_size()
        
        # return a boolean value, true if key is in, false if not
        def query(self, key):

            if str(key) in self.data:
                return True
            else:
                return False
    def register(self, message_handler, event_handler, module_handler):
        pass