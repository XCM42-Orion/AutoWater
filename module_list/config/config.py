from module import Module
import logger
import json
from event import *

class configInfo:
    def __init__(self, name, path, module, type, default):
        self.type = type
        self.name = name
        self.path = path
        self.data = None
        self.default = None
        self.module = module

class config(Module):

    def __init__(self):
        self.registered_config = []
        self.raw_config = None
        self.load_succeeded = False
        self.name_list = []
        
        self.register_config('target_groups')
        self.register_config('napcat_url')

        

    def load_config(self):
        config_path="config.json"
        with open(config_path, "r", encoding='utf-8') as f:
            try:
                self.raw_config = json.load(f)
                self.load_succeeded = True
            except json.JSONDecodeError as e:
                log = logger.Logger()
                log.warning(f"未能成功读取config.json:{e}，请检查是否存在语法错误")
                
                    

        for info in self.registered_config:
            path = info.path
            temp = self.raw_config

            sessions = path.split('.')
            succeed = True

            if len(sessions) == 1:
                try:
                    setattr(self, info.name, temp[sessions[0]])
                    self.name_list.append(info.name)
                except Exception as e:
                    log = logger.Logger()
                    log.warning(f"config'{info.name}'未能在'{info.path}'位置找到，已设置为默认值{str(info.default)}，将在稍后写入config.json")
                    setattr(self, info.name, info.default)

            for session in sessions[:-1]:
                try:
                    temp = temp[session]
                except:
                    log = logger.Logger()
                    log.warning(f"config'{info.name}'未能在'{info.path}'位置找到，已设置为默认值{str(info.default)}，将在稍后写入config.json")
                    setattr(self, info.name, info.default)
                    succeed = False
                    break

            if succeed:
                try:
                    setattr(self, info.name, temp[sessions[-1]])
                    self.name_list.append(info.name)
                except Exception as e:
                    log = logger.Logger()
                    log.warning(f"config'{info.name}'未能在'{info.path}'位置找到，已设置为默认值{str(info.default)}，将在稍后写入config.json")
                    
                    setattr(self, info.name, info.default)

    def __setattr__(self, name, value):
        if name != 'registered_config' and name != 'raw_config' and name != 'name_list':
            #self.set_config(name, value)
            pass
        return super().__setattr__(name, value)

    def update_config_value(self, name, value):
        """更新单个配置值"""
        #这是留给webui的接口
        try:
            # 获取配置项信息
            config_info = None
            for info in self.registered_config:
                if info.name == name:
                    config_info = info
                    break
            
            if not config_info:
                raise ValueError(f"配置项 {name} 未注册")
            
            # 根据类型转换值
            if config_info.type:
                if config_info.type == int:
                    value = int(value)
                elif config_info.type == float:
                    value = float(value)
                elif config_info.type == bool:
                    if isinstance(value, str):
                        value = value.lower() in ('true', '1', 'yes', 'y')
                    else:
                        value = bool(value)
                elif config_info.type == list:
                    if isinstance(value, str):
                        # 尝试解析JSON列表
                        try:
                            import json
                            value = json.loads(value)
                        except:
                            # 如果是逗号分隔的字符串
                            value = [v.strip() for v in value.split(',') if v.strip()]
            
            # 更新值
            setattr(self, name, value)
            
            # 保存到文件
            self.dump_config()
            
            return True
        except Exception as e:
            raise e
            return False

    def get_config(self, name=None):
        if name == None:
            return self.raw_config
        else:
            return self.__getattribute__(name)

    def get_registered_configs(self):
        """获取所有注册的配置项信息，按模块分组"""
        module_configs = {}
        
        for info in self.registered_config:
            module_name = info.module.__class__.__name__ if info.module else "global"
            
            if module_name not in module_configs:
                module_configs[module_name] = []
            
            # 获取当前值
            current_value = getattr(self, info.name, info.default)
            
            module_configs[module_name].append({
                'name': info.name,
                'path': info.path,
                'type': info.type.__name__ if info.type else type(current_value).__name__,
                'default': info.default,
                'current': current_value,
                'description': getattr(info, 'description', '')
            })
        
        return module_configs
    
    def dump_config(self):
        if not self.load_succeeded:
            return


        config_path="config.json"

        with open(config_path, "r", encoding='utf-8') as f:
            self.raw_config = json.load(f)

        for info in self.registered_config:
            path = info.path
            temp = self.raw_config

            info.data = self.__getattribute__(info.name)

            sessions = path.split('.')

            if len(sessions) == 1:
                self.raw_config[sessions[0]] = info.data
            
            else:
                temp = self.raw_config
                for session in sessions[:-1]:
                    temp = temp.setdefault(session, {})
                    
                temp[sessions[-1]] = info.data

        with open(config_path, "w", encoding='utf-8') as f:
            f.write(json.dumps(self.raw_config, indent=4, ensure_ascii=False))

    '''

            
        
        # WebSocket 配置
        self.napcat_url = config.get('napcat_url')
        self.target_groups = config.get('target_groups', [])
        
        # 回复配置
        self.set_emoji = config.get('set_emoji', [])
        self.set_reply = config.get('set_reply', [])
        self.keyword_reply = config.get('keyword_reply', [])
        self.random_reply = config.get('random_reply', [])
        self.ated_reply = config.get('ated_reply', [])
        
        # 概率配置
        self.keyword_possibility = config.get('keyword_possibility', 0)
        self.set_reply_possiblity = config.get("set_reply_possiblity", 0)
        self.emoji_possibility = config.get("emoji_possibility", 0)
        self.random_reply_possibility = config.get("random_reply_possibility", 0)
self.repeat_possibility = config.get("repeat_possibility", 0)
        self.at_possibility = config.get("at_possibility", 0)
        self.ated_reply_possibility = config.get("ated_reply_possibility", 0)
        self.poke_possibility = config.get("poke_possibility", 0)
        self.llm_possibility = config.get("llm_possibility", 0)
        
        # 定时回复功能
        self.do_report = config.get("do_report", False)
        self.time_reply = config.get('time_reply', [])
        
        # LLM配置
        llm_settings = config.get("llm_settings", {})
        self.background_message_number = llm_settings.get("background_message_number", 15)
        self.llm_url = llm_settings.get("url")
        self.llm_model = llm_settings.get("model")
        self.llm_apikey = llm_settings.get("apikey", "")
        self.llm_temperature = llm_settings.get("temperature", 1.0)
        self.llm_max_tokens = llm_settings.get("max_tokens", 100)
        self.llm_prompt = llm_settings.get("prompt", "")

        # heartflow 配置
        heartflow_settings = config.get("heartflow_settings", {})
        self.heartflow_api_url = heartflow_settings.get("api_url")
        self.heartflow_api_key = heartflow_settings.get("api_key")
        self.heartflow_model = heartflow_settings.get("model")
        self.heartflow_background_message_number = heartflow_settings.get("background_message_number", 15)
        self.heartflow_temperature = heartflow_settings.get("temperature", 1.0)
        self.heartflow_willing_weight = heartflow_settings.get("willing_weight", 0.3)
        self.heartflow_context_weight = heartflow_settings.get("context_weight", 0.3)
        self.heartflow_random_weight = heartflow_settings.get("random_weight", 0.1)
        self.heartflow_reply_threshold = heartflow_settings.get("reply_threshold", 0.5)
        self.heartflow_do_heartflow = heartflow_settings.get("do_heartflow", False)

        # 跟随贴表情配置
        self.follow_emoji = config.get("do_follow_emoji", False)
        self.follow_emoji_possibility = config.get("follow_emoji_possibility", 0)

        #贴表情自动回复配置
        self.do_emoji_threshold_reply = config.get("do_emoji_threshold_reply", False)
        self.emoji_threshold_reply = config.get("emoji_threshold_reply", [])
        self.emoji_threshold_reply_possibility = config.get("emoji_threshold_reply_possibility", 0)'''

    def register_config(self, name, path='', module=None, default=None,type=None):
        if name in self.name_list:
            return


        if default == None:
            if type == list:
                default = []
            elif type == float:
                default = float(0.0)
            elif type == int:
                default = 0
            elif type == str:
                default = ""
            elif type == dict:
                default = {}
            elif type == bool:
                default = False

        if path == '':
            path = name


        config_info = configInfo(name, path, module, type, default)
        config_info.default = default

        self.registered_config.append(config_info)

    async def run(self, event, context):
        self.load_config()

    def register(self, message_handler, event_handler, mod):
        message_handler.register_listener(self, EventType.EVENT_INIT, self.run, 100)

    def unregister(self):
        self.dump_config()
