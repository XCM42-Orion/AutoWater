import aiohttp
from collections import deque
from datetime import datetime

from module import *
from logger import Logger

from ast import Dict
from bs4 import BeautifulSoup
import requests
import hashlib
import platform

from urllib.parse import urlparse

from gmssl import sm2, func
import binascii

import json
import sys
from requests.utils import dict_from_cookiejar

import re
import uuid

import pickle

from InfoBot.const import *
from InfoBot.news.news import *

import asyncio

from llm.llm_utils import *
        
import html    

class InfoSession:
    def __init__(self,username,password):   
        self.session = requests.Session()
        self.csrf_token = ''
        self.default_headers = default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        }
        self.session.headers.update(default_headers)

        self.username = username

        self.password = password

        self.logged_in = False

        self.fingerprint = ''

        try:
            with open('fingerprint.pickle', 'rb') as f:
                self.fingerprint = pickle.load(f)
        except FileNotFoundError:
            self.fingerprint = uuid.uuid4().hex.replace('-', '')
            with open('fingerprint.pickle', 'wb') as fw:
                pickle.dump(self.fingerprint, fw)

    def get_redirect_url(self, url, data=None):
        response = self.session.post(url, data=data, allow_redirects=False)
        if response.status_code == 302:
            redirect_url = response.headers.get('Location')

        return redirect_url
        
    def fetch_public_key(self):
        public_key_response = self.session.get(WEB_VPN_OAUTH_LOGIN_URL, allow_redirects=False)
        if public_key_response.status_code == 302:
            webvpn_login_url = public_key_response.headers.get('Location')
            count = 0
            while True:
                login_response = self.session.get(webvpn_login_url, allow_redirects=False)
                if login_response.status_code == 302:
                    redirect_url = login_response.headers.get('Location')
                    webvpn_login_url = redirect_url
                    count += 1
                else:
                    soup = BeautifulSoup(login_response.text, 'html.parser')
                    input_element = soup.find(attrs={'id': 'sm2publicKey'})

                    sm2_public_key = input_element.text
                    
                    return sm2_public_key
        
        soup = BeautifulSoup(self.response.text, 'html.parser')
        input_element = soup.find(attrs={'id': 'sm2publicKey'})

        return input_element.text

    
    def encrypt_password(self, password, public_key):


        sm2_crypt = sm2.CryptSM2(
            private_key=None,
            public_key=public_key,
            mode=1,
            asn1=False
        )

        cypher_bytes = sm2_crypt.encrypt(password.encode('ascii'))
        
        #Turn the cypher bytes into hex string, and add prefix "04"
        encrypted_password = '04' + binascii.hexlify(cypher_bytes).decode('ascii')
        return encrypted_password
    
    def submit_login_form(self, username, encrypted_password):
        form_data = {
            'i_user': username,
            'i_pass': encrypted_password,
            'fingerPrint': self.fingerprint,
            'fingerGenPrint': '',
            'i_captcha': ''
        }

        request = self.session.post(ID_LOGIN_URL, data=form_data)
        return request.text

    def handle_two_factor_auth(self):
        two_factor_query = self.session.post(DOUBLE_AUTH_URL, data={
            'action': 'FIND_APPROACHES'
        })

        auth_method = input("请选择二次认证方式如'wechat' 'phone' 或 'totp'" + "可选:" + two_factor_query.text)
        two_auth_result = self.session.post(DOUBLE_AUTH_URL, data={
            "action": "SEND_CODE", 
            "type": auth_method  # "wechat" | "phone" | "totp"
        })

        if two_auth_result.status_code != 200:
            raise RuntimeError("二次认证方式选择失败，请检查输入是否正确。")
        
        code = input("请输入收到的验证码：")
        two_auth = self.session.post(DOUBLE_AUTH_URL, data={
            "action": ("VERITY_TOTP_CODE" if auth_method == "totp" else "VERITY_CODE"),
            "vericode": str(code),
        })

        if 'success' not in two_auth.text:
            raise RuntimeError("二次认证失败，请检查验证码是否正确。")
        
        cookies_dict = dict_from_cookiejar(self.session.cookies)
        with open("cookies.json", "w") as f:
            json.dump(cookies_dict, f)


        #I don't want to do 2FA again
        save_fingerprint = self.session.post(SAVE_FINGER_URL, data={
                    'fingerprint': self.fingerprint,
                    'deviceName': 'Autowater InfoBot Client',
                    'radioVal': "是"
        })


        if '上限' in save_fingerprint.text:
            print("保存设备指纹失败，达到保存上限。")

        data = two_auth.json()
        
        redirect_url =  "https://id.tsinghua.edu.cn" + data["object"]["redirectUrl"]

        login_url = self.session.get(redirect_url)
        
        
        soup = BeautifulSoup(login_url.text, 'html.parser')
        link = soup.find('a')
        redirect_url = link.get('href')


        return redirect_url
    
    def handle_response(self, redirect_url):
        redirect = self.session.post(redirect_url)
        return redirect.text
    
    def get_csrf_token(self):
        cookies = self.session.post(GET_COOKIE_URL)


        match = re.search(r'XSRF-TOKEN=([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', cookies.text)

        if match:
            return match.group(1)
        else:
            self.login()
            cookies = self.session.post(GET_COOKIE_URL)
            match = re.search(r'XSRF-TOKEN=([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', cookies.text)
            if match:
                return match.group(1)
            else:
                raise RuntimeError("CSRF token not found in cookies.")
        
    def parse_url(self, url_in):
        """将原始URL转换为WebVPN URL（根据parseUrl函数）"""
        
        # 检查IP地址格式：http://IP:PORT/path
        raw_res = re.search(r'http://(\d+\.\d+\.\d+\.\d+):(\d+)/(.+)', url_in)
        if raw_res:
            ip = raw_res.group(1)
            port = raw_res.group(2)
            path = raw_res.group(3)
            # 需要IP到HOST_MAP的映射，这里假设有
            return f"https://webvpn.tsinghua.edu.cn/http-{port}/{HOST_MAP.get(ip, 'unknown')}/{path}"
        
        # 检查 *.tsinghua.edu.cn 格式
        protocol = url_in.split(':')[0]  # http or https
        reg_res = re.search(r'://(.+?)\.tsinghua\.edu\.cn(?::(\d+))?/(.+)', url_in)
        if reg_res:
            host = reg_res.group(1)
            port = reg_res.group(2) if reg_res.group(2) else None
            path = reg_res.group(3)
            
            protocol_full = protocol
            if port:
                protocol_full = f"{protocol}-{port}"
            elif protocol == "https":
                protocol_full = "https"
            else:
                protocol_full = "http-80"
            
            host_code = HOST_MAP.get(host, None)
            if not host_code:
                # 如果没有映射，尝试用默认方式
                return url_in
            
            return f"https://webvpn.tsinghua.edu.cn/{protocol_full}/{host_code}/{path}"
        
        # 如果都不匹配，返回原URL
        return url_in
    
    def get_webvpn_url(self, url_in):
        """根据getWebVPNUrl函数生成WebVPN URL"""
        if "oauth.tsinghua.edu.cn" in url_in:
            return url_in
        
        from urllib.parse import urlparse, urlencode, unquote
        
        url = urlparse(url_in)
        scheme = url.scheme
        host = url.hostname
        port = url.port or (443 if scheme == "https" else 80)
        
        # 构建URI
        uri = url.path
        if url.query:
            uri += f"?{url.query}"
        if url.fragment:
            uri += f"#{url.fragment}"
        
        # 构建跳转URL
        params = {
            'scheme': scheme,
            'host': host,
            'port': port,
            'uri': uri
        }
        params = unquote(urlencode(params))
        
        return f"https://oauth.tsinghua.edu.cn/lb-auth/lbredirect?{params}"
    
    def roam(self, policy, payload, username, password):
        """模拟原JavaScript中的roam函数（仅实现id策略）"""
        if policy == "id":

            target_url = f"{ID_BASE_URL}{payload}"

            webvpn_target_url = target_url

            response = self.session.get(webvpn_target_url)

            soup = BeautifulSoup(response.text, 'html.parser')
            sm2_public_key_element = soup.find('div', {'id': 'sm2publicKey'})
            
            if not sm2_public_key_element:
                if "登录成功" in response.text or "欢迎" in response.text:
                    return response.text
                
                raise RuntimeError("Failed to get public key in roam")
            
            sm2_public_key = sm2_public_key_element.text
            
            # 加密密码
            encrypted_password = self.encrypt_password(password, sm2_public_key)   

            webvpn_login_url = self.get_webvpn_url(ID_LOGIN_URL)
            
            form_data = {
                'i_user': username,
                'i_pass': encrypted_password,
                'fingerPrint': self.fingerprint,
                'fingerGenPrint': '',
                'i_captcha': ''
            }
            
            # 注意：这里访问的是跳转URL，可能需要处理重定向
            count = 0
            while True:
                login_response = self.session.post(webvpn_login_url, data=form_data, allow_redirects=False)
                if login_response.status_code == 302:
                    redirect_url = login_response.headers.get('Location')
                    webvpn_login_url = redirect_url
                    count += 1
                else:
                    break
            
            # 处理响应
            response_text = login_response.text
            
            
            # 检查是否需要二次认证
            if '二次认证' in response_text:
                print("roam过程中需要二次认证")
                redirect_url = self.handle_two_factor_auth()
                return self.handle_response(redirect_url)
            
            # 检查登录结果
            if '登录成功' in response_text or '正在重定向' in response_text:
                pass
            else:
                print("roam登录失败")
                return response_text
            # 提取重定向链接
            soup = BeautifulSoup(response_text, 'html.parser')
            link = soup.find('a')
            
            if link and link.get('href'):
                redirect_url = link.get('href')

                if policy != "card":
                    redirect_url = self.get_webvpn_url(redirect_url)


                final_response = self.session.get(redirect_url)
                return final_response.text
        
        else:
            raise NotImplementedError(f"Policy {policy} not implemented")
        
    def login(self):
        sm2_public_key = self.fetch_public_key()
    
        try:
            with open("cookies.json", "r") as f:
                cookies_dict = json.load(f)
                self.session.cookies.update(cookies_dict)
        except FileNotFoundError:
            pass

        if sm2_public_key != '':
            encrypted_password = self.encrypt_password(self.password, sm2_public_key)
            response_text = self.submit_login_form(self.username, encrypted_password)
            redirect_url = ""
            if '二次认证' in response_text:
                redirect_url = self.handle_two_factor_auth()

            else:
                soup = BeautifulSoup(response_text, 'html.parser')
                link = soup.find('a')
                redirect_url = link.get('href')
            self.handle_response(redirect_url)
        else:
            raise RuntimeError("Failed to fetch public key.")
        
        #Access the default page to get the csrf token

        self.roam("id", "10000ea055dd8d81d09d5a1ba55d39ad", self.username, self.password)
        self.csrf_token = self.get_csrf_token()

        self.logged_in = True



class InfoBotCore(Module):
    prerequisite = ['config', 'llm']


    def __init__(self):
        self.config = None
        self.recent_messages = None
        self.logger = Logger()

        self.context = None

        self.infosession = None

    def register(self, message_handler, event_handler, mod):
        self.config = mod.config
        self.context = event_handler.apply_for_context(self)
        self.infosession = InfoSession('','')#(self.config.username, self.config.password)

        self.infosession.login()


        self.bot_news = InfoBotNewsWrapper(self.infosession)

        mod.llm.register_tool(LLMTool('get_news_list','获取清华官方网站新闻列表',[LLMToolArgument("integer","page","新闻列表页码，一页20条")],self.bot_news.on_get_news_list))
        mod.llm.register_tool(LLMTool('get_news_details','获取清华官方网站新闻详细信息',[LLMToolArgument("integer","index","新闻序号，范围0-19，不要每次都选一样的")],self.bot_news.on_get_news_details))
    






















    
    