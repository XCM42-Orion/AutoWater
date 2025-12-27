from dataclasses import dataclass
from typing import Dict, Optional
import base64
import io
from PIL import Image
import requests
    
def get_image_from_url(url: str, format: str = 'JPEG'):
    """从URL下载图片并存储"""
    response = requests.get(url)
    response.raise_for_status()
    image_bytes = response.content
    
    # 预处理图片
    img = Image.open(io.BytesIO(image_bytes))
    output_buffer = io.BytesIO()
    img.save(output_buffer, format=format, optimize=True, quality=85)
    
    return output_buffer.getvalue()

def get_base64(image):
    """获取base64编码"""
    # 如果缓存中没有，则计算并缓存
    return base64.b64encode(image).decode('utf-8')

@dataclass
class MessageImage:
    def __init__(self, url):
        #self.bytes = get_image_from_url(url)
        self.url = url
        #self.base64 = get_base64(self.bytes)