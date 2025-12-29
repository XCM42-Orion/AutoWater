import asyncio
from datetime import datetime,time
from module import Module
from message_utils import *
from logger import Logger

import threading

import json
import os
from typing import Any, Dict

import module_list.webui.flask_app as flask_app

class webui(Module):

    prerequisite = ['config']

    def __init__(self):
        self.context = None
        self.config_manager = None
        self.module_manager = None
        self.flask_app = None
        self.logger = Logger()
        pass
    
    def register(self,message_handler,event_handler,module_handler):
        message_handler.register_listener(self, EventType.EVENT_INIT, self.run)
        #module_handler.config.register_config('time_reply', module=self)
        #module_handler.config.register_config('do_report', module=self)


    def run(self, event, context):
        """flask app启动，并申请context，初始化ConfigManager"""

        self.context = context.event_handler.apply_for_context(self)

        self.config_manager = ConfigManager(self.context.mod.config)
        self.module_manager = ModuleManager(self.context.mod)
        self.flask_app = flask_app.FlaskApp(self.config_manager, self.module_manager)
        self.logger.debug(f"Autowater Webui 已启动。url: http://{self.flask_app.host}:{self.flask_app.port}/")



"""
配置管理类
用于加载、保存和管理应用配置
"""

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config = config
    
    
    def save_config(self):
        """保存配置到文件"""
        self.config.dump_config()
    
    def get_config(self):
        """获取当前配置"""
        return self.config.raw_config
    
    def update_config(self, new_config: Dict[str, Any]):
        success = True
        for name, value in new_config.items():
            if not self.config.update_config_value(name, value):
                success = False
        
        if success:
            self.config.dump_config()
        
        return success
    
    def get_value(self, name: str, default: Any = None) -> Any:
        """获取指定配置值，支持点表示法访问嵌套字典"""
        return self.config.get_config(name)
    
    def get_registered_configs(self):
        """获取所有注册的配置项，按模块分组"""
        return self.config.get_registered_configs()
    

class ModuleManager:
    def __init__(self, module_handler):
        #with open('settings.json', "r", encoding='utf-8') as f:
            #settings = json.load(f)


        self.module_handler = module_handler

    def get_all_modules(self):
        return self.module_handler.loaded_modules