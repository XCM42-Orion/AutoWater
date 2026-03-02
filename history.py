from event import *
from module import *
from enum import Enum
from typing import *


class ActionType:
    ACTION_RETURN = 0  #对应某个listener的处理结果,data是返回值
    ACTION_MSG_SEND = 1 #对应send_message被调用,data是一个Message对象
    #注意上面的action中对应的是发送的原始数据，它可能会被listener修改，最终数据要从EVENT_SEND_MSG获得 



#每一个Action结构储存一个历史行为
class Action:
    def __init__(self, action_type: ActionType, data: Any, actioner: Module, action_event: Event):
        self.action_type = action_type
        self.data = data
        self.actioner = actioner
        #此action发生时对应的事件
        self.action_event = action_event

#每一个History结构储存一段时间内的历史行为
class History:
    def __init__(self):
        pass