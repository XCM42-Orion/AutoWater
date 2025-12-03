import json

class Config:
    def __init__(self, config_path="config.json"):
        with open(config_path, "r", encoding='utf-8') as f:
            config = json.load(f)
        
        # WebSocket 配置
        self.napcat_url = config.get('napcat_url')
        self.target_groups = config.get('target_groups', [])
        
        # 回复配置
        self.set_emoji = config.get('set_emoji', [])
        self.set_reply = config.get('set_reply', [])
        self.keyword_reply = config.get('keyword_reply', [])
        self.random_reply = config.get('random_reply', [])
        self.ated_reply = config.get('ated_reply', [])
        self.time_reply = config.get('time_reply', [])
        
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
        
        # 功能开关
        self.do_report = config.get("do_report", False)
        
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