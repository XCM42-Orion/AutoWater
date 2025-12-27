import numpy as np
import sys
from text2vec import SentenceModel
from text2vec import Word2Vec
from numpy.linalg import norm


model = "shibing624/text2vec-base-chinese"
t2v_model = SentenceModel(model)

class VectorizedChatHistoryManager:
    def __init__(self, limit = 50000):
        self.matrix = None
        self.message_ids = []
        self.limit = limit

    def add_sentence(self, sentence, message_id):
        vector = self.convert_to_vector(sentence)
        if self.matrix is None:
            self.matrix = vector.reshape(1, -1)
        else:
            self.matrix = np.vstack((self.matrix, vector))

        self.message_ids.append(message_id)

        if self.matrix.shape[0] > self.limit:
            self.matrix = np.delete(self.matrix, 0, axis=0)
            del self.message_ids[0]

        return vector

    def calc_similarity(self, vector):
        norms = np.linalg.norm(self.matrix, axis=1, keepdims=True)
        eps = 1e-8
        normalized = self.matrix / (norms + eps)

        vector = vector.reshape(1, -1)

        vector_norm = np.linalg.norm(vector)

        normalized_vector = (vector / (vector_norm + eps)).T

        similarity_vector = np.dot(normalized, normalized_vector).reshape(1, -1)

        return similarity_vector.flatten()
    
    def top_k_similarity(self, similarity_vector, k):
        try:
            indices = np.argpartition(similarity_vector, -k)[-k:] # 获取部分排序的索引
            sorted_indices = indices[np.argsort(similarity_vector[indices])] # 对前 K 项排序

            top_k_values = similarity_vector[sorted_indices]

            return list(reversed(sorted_indices)),list(reversed(top_k_values))
        except:
            return None

    def convert_to_vector(self, sentence):
        sentence_embedding = t2v_model.encode(sentence)
        return sentence_embedding
    
    def get_vectors_from_message_ids(self, message_id_list):
        indexes = []
        for each in message_id_list:
            indexes.append(self.message_ids.index(each))

        if indexes != []:
            return self.matrix[indexes]
        
    def get_vectors_from_chat_history(self, chat_history_list):
        message_id_list = []
        for chat_history in chat_history_list:
            message_id_list.append(chat_history.message.message_id)

        return self.get_vectors_from_message_ids(message_id_list)