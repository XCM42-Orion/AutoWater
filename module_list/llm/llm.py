import aiohttp
from collections import deque
from datetime import datetime
from module import *
from typing import *
from event import *
from logger import Logger
from llm_utils import *

import json

import asyncio



class llm(Module):
    prerequisite = ['config']


    def __init__(self):
        self.config = None
        self.recent_messages = None
        self.logger = Logger()

        self.tools = []
        self.tool_callbacks = dict()
        self.llm_instance = None

    def register(self, message_handler, event_handler, mod):
        self.config = mod.config

        self.config.register_config('llm_background_message_number', 'llm_settings.background_message_number', module=self)
        self.config.register_config('llm_url', 'llm_settings.url', module=self)
        self.config.register_config('llm_model', 'llm_settings.model', module=self)
        self.config.register_config('llm_apikey', 'llm_settings.apikey', module=self)
        self.config.register_config('llm_temperature', 'llm_settings.temperature', module=self)
        self.config.register_config('llm_max_tokens', 'llm_settings.max_tokens', module=self)
        self.config.register_config('llm_prompt', 'llm_settings.prompt', module=self)
        self.config.register_config('llm_is_multimodal', 'llm_settings.multimodal', module=self)
        self.config.register_config('llm_thinking', 'llm_settings.thinking', module=self)
    
        message_handler.register_listener(self, EventType.EVENT_INIT, self.on_init)
        message_handler.register_listener(self, EventType.EVENT_RECV_MSG, self.on_recv_msg, 800)

    def register_tool(self, tool):
        self.llm_instance.add_tool(tool)

    async def on_init(self, event, context):
        self.recent_messages = deque(maxlen=self.config.llm_background_message_number)
        llm_config = LLMConfig(self.config.llm_model,
                               self.config.llm_prompt,
                               self.config.llm_url,
                               self.config.llm_apikey,
                               self.config.llm_temperature,
                               self.config.llm_max_tokens,
                               self.config.llm_thinking,
                               llm_capabilities=LLMCapabilities(self.config.llm_is_multimodal),
                               set_as_default_config=True)
        self.llm_instance = LLMInstance(self, llm_config)
    
    async def call_llm(self, tool_calling=True, tool_choice='auto', prompt_annotation=None, prompt=None):
        """调用LLM API"""
        prompt = self.config.llm_prompt if prompt == None else prompt
        prompt = prompt + (('\n' + prompt_annotation) if prompt_annotation != None else "")
        self.llm_instance.config.llm_prompt = prompt
        return await self.llm_instance.call_llm(tool_calling, tool_choice)
        
    async def on_recv_msg(self, event, context):
        message = event.data
        config = context.mod.config
        message_handler = context.message_handler

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