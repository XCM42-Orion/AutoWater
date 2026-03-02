from enum import Enum

from archive.archive_utils import *
from embedding.embedding_utils import *

class ChunkingState(Enum):
    CHUNKING_ACTIVE = 0
    CHUNKING_NEW = 1
    CHUNKING_PENDING = 2

class Chunk:
    count = 0
    def __init__(self):
        self.chat_history = []
        self.chunk_id = Chunk.count
        self.active = True
        Chunk.count += 1

    def add_chat_history(self, chat_history):
        self.chat_history.append(chat_history)

    def inactivate(self):
        self.active = False

    def activate(self):
        self.active = True


class ChunkingMachine:
    def __init__(self):
        pass