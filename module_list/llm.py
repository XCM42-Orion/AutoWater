import aiohttp
from collections import deque
from datetime import datetime
from module import *
from typing import *
from logger import Logger

import json

import asyncio

class LLMToolArgument:
    def __init__(self, type: str, name:str, description: str, required: bool=True):
        self.type = type
        self.name = name
        self.description = description
        self.required = required

class llm(Module):
    prerequisite = ['config']


    def __init__(self):
        self.config = None
        self.recent_messages = None
        self.logger = Logger()

        self.tools = []
        self.tool_callbacks = dict()

    def register(self, message_handler, event_handler, mod):
        self.config = mod.config
        self.recent_messages = deque(maxlen=self.config.background_message_number)
    
    def add_message_to_history(self, user_id, sender, text):
        """添加消息到历史记录"""
        self.recent_messages.append({
            "user_id": user_id,
            "sender": sender,
            "time": datetime.now().isoformat(),
            "text": text
        })

    def register_tool(self, tool_name: str,tool_description: str,properties: List[LLMToolArgument], callback: Callable) -> int:
        '''注册一个llm工具，返回工具id。注意callback的参数名要与properties里面的参数名相同'''
        '''回调函数的返回值应该是一个json形式的字典'''
        new_tool = {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": tool_description,
            "parameters": {
                "type": "object",
                "properties": dict()
            }

        }
    }
        for each_argument in properties:
            new_tool["function"]["parameters"]["properties"][each_argument.name] = {"type":each_argument.type,"description":each_argument.description}

        new_tool["function"]["parameters"]["required"] = [each_argument.name for each_argument in properties if each_argument.required]

        self.tools.append(new_tool)

        self.tool_callbacks[tool_name] = callback

        return len(self.tools) - 1
    
    async def call_llm(self, user_msg, user_id=None, nickname=None, tool_calling=True, tool_choice='auto'):
        """调用LLM API"""
        messages = []
        messages.append({
            "role": "system",
            "content": self.config.llm_prompt
        })
        
        # 添加上下文消息
        if self.recent_messages:
            for msg in self.recent_messages:
                display_name = f"{msg['sender']}({msg['user_id']})"
                messages.append({
                    "role": "user",
                    "content": f"{display_name}: {msg['text']}"
                })
        
        # 当前用户消息
        if user_id and nickname:
            display_name = f"{nickname}({user_id})"
            messages.append({"role": "user", "content": f"{display_name}: {user_msg}"})
        else:
            messages.append({"role": "user", "content": user_msg})
        
        payload = {
            "model": self.config.llm_model,
            "messages": messages,
            "stream": False,
            "temperature": self.config.llm_temperature,
            "max_tokens": self.config.llm_max_tokens
        }

        if tool_calling:
            payload["tools"] = self.tools
            payload["tool_choice"] = tool_choice
        
        headers = {
            "Authorization": f"Bearer {self.config.llm_apikey}",
            "Content-Type": "application/json"
        }

        self.logger.info("开始调用LLM接口")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.config.llm_url, headers=headers, json=payload) as resp:
                    resp.raise_for_status()
                    result = await resp.json()
                    message = result["choices"][0]["message"]
                    messages.append(message)

                    max_count = 20
                    count = 0
                    while tool_calling and ("tool_calls" in message) and (count <= max_count):
                        for tool_call in message["tool_calls"]:
                            tool_name = tool_call["function"]["name"]
                            tool_args = json.loads(tool_call["function"]["arguments"])

                            self.logger.info(f"工具{tool_name}被调用，参数{tool_args}")


                            ret = None
                            try:
                                if asyncio.iscoroutinefunction(self.tool_callbacks[tool_name]):
                                    ret = await self.tool_callbacks[tool_name](**tool_args)
                                else:
                                    ret = self.tool_callbacks[tool_name](**tool_args)
                                
                                if not isinstance(ret, (dict, list, str, int, float, bool, type(None))):
                                    ret = str(ret)
                                    
                            except Exception as e:
                                self.logger.error(f"工具{tool_name}执行失败: {e}")
                                ret = {"error": str(e)}


                            self.logger.info(f"工具{tool_name}已调用，返回长度{len(ret)}")

                            processed_ret = json.dumps(ret, ensure_ascii=False)
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "content": processed_ret
                            })
                            

                        payload["messages"] = messages
                        new_response = await session.post(self.config.llm_url, headers=headers, json=payload)
                        new_response.raise_for_status()
                        new_result = await new_response.json()
                        self.logger.info(f"工具调用结果已经返回给llm")
                        message = new_result["choices"][0]["message"]
                        
                        messages.append(message)

                        count += 1

                    
                    raw_str = message["content"]

                    self.logger.info(f"LLM返回原始内容: {raw_str}")
                    return raw_str.split('%n')
        except Exception as e:
            self.logger.error(f"LLM调用失败: {e}")
            return []
        
    async def on_recv_msg(self, event, context):
        message = event.data
        config = context.mod.config
        message_handler = context.message_handler

        self.add_message_to_history(message.user_id, message.nickname, str(message))