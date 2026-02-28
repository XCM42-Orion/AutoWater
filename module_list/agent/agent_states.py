from enum import Enum
from typing import Literal

class ChatState(Enum):
    NORMAL = 0
    COLD_CHAT = 1
    ACTIVE_CHAT = 2
    SILENT = 3
    ERROR = 4

class ActionState(Enum):
    READY = 0
    PENDING = 1
    SUCCESSFUL = 2
    FAILED = 3

class Notification(Enum):
    NEW_MESSAGE = 0
    COLD_CHAT = 1
    ACTIVE_CHAT = 2
    ERROR = 3

'''
智能体的一步行动

Args:
    reason: 本次行动原因
    result: 本次行动结果
    action_type: 行动类型


'''
class AgentAction:
    def __init__(self, action_type: Literal["fetch_knowledge",
                                            "wait",
                                            "listening",
                                            "send_new_message",
                                            "rethink_goal",
                                            "end_conversation"], reason: str):
        self.action_type = action_type
        self.reason = reason

        self.result = None
        self.action_state: ActionState = ActionState.READY

    def change_state(self, new_state: ActionState, result: str=None):
        self.action_state = new_state
        self.result = result

class AgentState:
    def __init__(self, inital_goal: str, personality: str):
        self.goal = inital_goal
        self.personality = personality

        self.knowledge_info = None
        self.action_history_summary = None
        self.last_action_summary = None

        self.time_since_last_bot_message = -1

        self.chat_history = None

