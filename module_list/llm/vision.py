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



class vision_llm(Module):
    prerequisite = ['config', 'storage']


    def __init__(self):
        self.config = None
        self.recent_messages = None
        self.logger = Logger()

        self.tools = []
        self.deployed = None
        self.tool_callbacks = dict()
        self.cache = {}
        self.llm_instance = None

        self.storage = None

    def register(self, message_handler, event_handler, mod):
        self.config = mod.config
        self.storage = mod.storage

        self.config.register_config('vllm_background_message_number', 'vllm_settings.background_message_number', module=self)
        self.config.register_config('vllm_enable', 'vllm_settings.enable', module=self)
        self.config.register_config('vllm_url', 'vllm_settings.url', module=self)
        self.config.register_config('vllm_model', 'vllm_settings.model', module=self)
        self.config.register_config('vllm_apikey', 'vllm_settings.apikey', module=self)
        self.config.register_config('vllm_temperature', 'vllm_settings.temperature', module=self)
        self.config.register_config('vllm_max_tokens', 'vllm_settings.max_tokens', module=self)
        self.config.register_config('vllm_prompt', 'vllm_settings.prompt', module=self)
        self.config.register_config('vllm_is_multimodal', 'vllm_settings.multimodal', module=self)
        self.config.register_config('vllm_thinking', 'vllm_settings.thinking', module=self)

        message_handler.register_listener(self, EventType.EVENT_INIT, self.on_init)

    def register_tool(self, tool):
        self.llm_instance.add_tool(tool)

    async def on_init(self, event, context):
        self.recent_messages = deque(maxlen=self.config.vllm_background_message_number)
        self.deployed = self.config.vllm_enable
        llm_config = LLMConfig(self.config.vllm_model,
                               self.config.vllm_prompt,
                               self.config.vllm_url,
                               self.config.vllm_apikey,
                               self.config.vllm_temperature,
                               self.config.vllm_max_tokens,
                               self.config.vllm_thinking,
                               llm_capabilities=LLMCapabilities(self.config.vllm_is_multimodal))
        self.llm_instance = LLMInstance(self, llm_config)
    
    async def call_vllm(self, image, tool_calling=True, tool_choice='auto', prompt_annotation=None, prompt=None):
        """调用LLM API"""
        self.cache = self.storage.permanent(self.cache, self, "image_cache")
        if self.cache.get(image.url, None):
            return self.cache[image.url]
        prompt = self.config.vllm_prompt if prompt == None else prompt
        prompt = prompt + (('\n' + prompt_annotation) if prompt_annotation != None else "")
        self.llm_instance.config.vllm_prompt = prompt
        self.llm_instance.add_image_to_history("user", image)
        result = await self.llm_instance.call_llm(False, None)
        self.llm_instance.pop_last()
        self.cache[image.url] = result
        return result