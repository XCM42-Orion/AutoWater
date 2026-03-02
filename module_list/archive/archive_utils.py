from typing import List, Dict

class Person:
    def __init__(self, qqid : int, nickname : str, unknown : bool=False):
        self.qqid = int(qqid)
        self.nickname = str(nickname)
        self.unknown = unknown

class PersonManager:
    def __init__(self):
        self.people = {}

    def add_person(self, person):
        self.people[person.qqid] = person

    def find_person_by_qqid(self, qqid):
        return self.people.get(qqid, Person(qqid, "", unknown=True))
    
    def delete_person(self, qqid):
        del self.people[qqid]

    def update_nickname(self, qqid, nickname):
        self.people[qqid].nickname = nickname

import time



class ChatHistory:
    def __init__(self, message, sender):
        self.message = message
        self.time_stamp = time.time()
        self.sender = sender

    def __str__(self):
        local_time = time.localtime(self.time_stamp)
        formatted_time = time.strftime("%m-%d %H:%M:%S", local_time)
        name = ""
        if self.sender != None:
            name = f"用户(“{self.sender.nickname}”)"
        else:
            name = f"用户({self.sender.qqid})"
        return str(name) + '在' + formatted_time + '发送的消息:“' + str(self.message) + "”"

class ChatHistoryManager:
    def __init__(self, limit=10000):
        self.chat_history = {}
        self.chat_history_list = []
        self.limit = 10000
        self.count = 0

    def add_message(self, chat_history):
        message_id = chat_history.message.message_id
        self.chat_history[message_id] = chat_history
        self.chat_history_list.append(chat_history)
        if self.count == 10000:
            oldest_message_id = self.chat_history_list[0]
            del self.chat_history_list[0]
            del self.chat_history[oldest_message_id]
        else:
            self.count += 1

    def find_message_by_message_id(self, message_id):
        return self.chat_history.get(message_id, None)

    def find_around(self, message_id, radius):
        try:
            index = self.chat_history_list.index(self.find_message_by_message_id(message_id))
        except ValueError:
            return None
        start = max(index - radius, 0)
        end = min(index + radius + 1, self.limit - 1)

        return self.chat_history_list[start:end]
    
    def find_by_keyword(self, keyword):
        matched = []
        for message_id, chat_history in self.chat_history.items():
            if keyword in str(chat_history.message):
                matched.append(message_id)

        return matched
    
    def find_chat_history_from_message_ids(self, message_id_list):
        chat_history_list = []
        for message_id in message_id_list:
            chat_history = self.find_message_by_message_id(message_id)
            if chat_history != None:
                chat_history_list.append(chat_history)
        return chat_history_list