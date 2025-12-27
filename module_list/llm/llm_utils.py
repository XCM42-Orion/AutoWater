

import aiohttp
from collections import deque
from datetime import datetime
from module import *
from typing import *
from event import *
from logger import Logger

import json

import asyncio


class LLMToolArgument:
    def __init__(self, type: str, name:str, description: str, required: bool=True):
        self.type = type
        self.name = name
        self.description = description
        self.required = required



class LLMTool:
    def __init__(self, tool_name, tool_description, arguments, callback, public=True):
        '''注册一个llm工具，返回工具id。注意callback的参数名要与properties里面的参数名相同'''
        '''回调函数的返回值应该是一个json形式的字典'''
        '''参数public=True的tool会被注册入工具箱(toolkit)，从而可以被快速使用'''
        self.tool_name = None
        self.tool_descriptipn = None
        self.arguments = None
        self.callback = None
        self.payload = None

        self.make_tool(tool_name, tool_description, arguments, callback, public)


    def make_tool(self, tool_name, tool_description, arguments, callback, public):
        '''注册一个llm工具。注意callback的参数名要与properties里面的参数名相同'''
        '''回调函数的返回值应该是一个json形式的字典'''
        self.tool_name = tool_name
        self.tool_descriptipn = tool_description
        self.arguments = self.arguments
        self.callback = callback
        self.payload = {
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

        for each_argument in arguments:
            self.payload["function"]["parameters"]["properties"][each_argument.name] = {"type":each_argument.type,"description":each_argument.description}

        self.payload["function"]["parameters"]["required"] = [each_argument.name for each_argument in arguments if each_argument.required]

        if public:
            LLMToolkit.add_tool(self)


class LLMToolkit:
    tools = {}

    def delete_tool(name):
        del LLMToolkit.tools[name]

    def add_tool(tool):
        LLMToolkit.tools[tool.tool_name] = tool

class LLMCapabilities:
    def __init__(self, multimodal):
        self.multimodal = multimodal

class LLMConfig:
    default_config = None
    def __init__(self, llm_model, llm_prompt, llm_url, llm_apikey, llm_temperature, llm_max_tokens, thinking=False, llm_capabilities=None, set_as_default_config=False):
        self.llm_model = llm_model
        self.llm_prompt = llm_prompt
        self.llm_apikey = llm_apikey
        self.llm_url = llm_url
        self.llm_temperature = llm_temperature
        self.llm_max_tokens = llm_max_tokens
        self.thinking = thinking
        if llm_capabilities == None:
            llm_capabilities = LLMCapabilities(False)
        self.llm_capabilities = llm_capabilities       

        if set_as_default_config:
            LLMConfig.default_config = self

class LLMInstance:
    def __init__(self, module, llm_config=None):
        '''llm_config=None时，使用默认llm配置'''
        if llm_config is None:
            llm_config = LLMConfig.default_config
        self.config = llm_config
        self.tool_callbacks = {}
        self.module = module
        self.tools = []
        self.recent_messages = []
        self.logger = Logger()

    def add_message_to_history(self, sender, text, timestamp=None):
        """添加消息到历史记录"""
        formatted_time = None
        if timestamp == None:
            formatted_time = datetime.now().isoformat()
        else:
            formatted_time = datetime.fromtimestamp(timestamp).isoformat()

        self.recent_messages.append({
            "sender": sender,
            "time": formatted_time,
            "type": "text",
            "text": text
        })

    def add_image_to_history(self, sender, image, timestamp=None):
        formatted_time = None
        if timestamp == None:
            formatted_time = datetime.now().isoformat()
        else:
            formatted_time = datetime.fromtimestamp(timestamp).isoformat()

        
        self.recent_messages.append({
            "sender": sender,
            "time": formatted_time,
            "type": "image",
            "image": image
        })

    def add_from_chat_history(self, chat_history_list):
        for chat_history in chat_history_list:
            message = chat_history.message
            images = []
            has_text = False
            for each_component in message.get_components():
                if each_component.type == "image":
                    images.append(each_component.data)
            else:
                has_text = True

            if has_text:
                self.llm_instance.add_message_to_history(f"{message.nickname}({message.user_id})", str(message))
            
            if self.config.llm_is_multimodal:
                for each_image in images:
                    self.llm_instance.add_image_to_history(f"{message.nickname}({message.user_id})", each_image)

    def pop_last(self):
        self.recent_messages.pop()

    def add_tool(self, tool: LLMTool):
        self.tools.append(tool.payload)
        self.tool_callbacks[tool.tool_name] = tool.callback

    def delete_tool(self, name):
        index = 0
        for each in self.tools:
            if each.tool_name == name:
                break
            index += 1

        del self.tools[index]
        del self.tool_callbacks[name]

    def add_tools(self, tool_lists):
        if isinstance(tool_lists, Iterable):
            for each_tool in tool_lists:
                self.add_tool(each_tool)

        elif isinstance(tool_lists, UsingTools):
            for each_tool in tool_lists.get_tools():
                self.add_tool(each_tool)
    
    async def call_llm(self, tool_calling=True, tool_choice='auto'):
        """调用LLM API"""
        messages = []
        messages.append({
            "role": "system",
            "content": self.config.llm_prompt
        })
        
        # 添加上下文消息
        if self.recent_messages:
            for msg in self.recent_messages:
                if msg['type'] == "text":
                    display_name = f"{msg['sender']}"
                    messages.append({
                        "role": "user",
                        "content": f"{display_name}: {msg['text']}"
                    })
                elif msg['type'] == "image":
                    messages.append({
                            "role": "user",
                            "content": [{
                            "type": "image_url",
                            "image_url": {
                                "url": msg["image"].url
                            }
                    }]})
        
        payload = {
            "model": self.config.llm_model,
            "messages": messages,
            "stream": False,
            "temperature": self.config.llm_temperature,
            "max_tokens": self.config.llm_max_tokens
        }

        if not self.config.thinking:
            payload["thinking"] = {
            "type": "disabled"
        }
            
        else:
            payload["thinking"] = {
            "type": "enabled"
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

                    
                    raw_str = message["content"] if not self.config.thinking else message["reasoning_content"]
                    
                    self.logger.info(f"LLM返回原始内容: {raw_str}")
                    return raw_str.split('%n')
        except Exception as e:
            self.logger.error(f"LLM调用失败: {e}")
            return []

class UsingTools:
    def __init__(self, name_list):
        if name_list != '*':
            self.tools = [t for t in LLMToolkit.tools if t.tool_name in name_list]
        else:
            self.tools = LLMToolkit.tools
        
    def get_tools(self):
        for each in self.tools:
            yield each