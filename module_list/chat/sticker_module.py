import json
from PIL import Image,ImageFile
import websockets
from event import Event, EventContext, EventType
import logger
import asyncio
import aiohttp
import os
from urllib.request import urlretrieve
from enum import Enum
from module import Module
from message_utils import Message, MessageComponent
from module_list.archive.archive import archive
from message_image import get_base64

class SymDir(Enum):
    LEFT_TO_RIGHT = 0
    RIGHT_TO_LEFT = 1
    UP_TO_DOWN = 2
    DOWN_TO_UP = 3

logg = logger.Logger()

def dl_image(url:str, filename:str):

    urlretrieve(url,filename)
    return Image.open(filename)
    '''
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            with open(filename, "wb") as f:
                while True:
                    chunk = await response.content.readany()
                    if not chunk:
                        break
                    f.write(chunk)
                print(f"Downloaded {filename} from {url}")
                '''

def merge(im1: Image.Image, im2: Image.Image, direction:int = 0) -> Image.Image:
    '''
    merge two PIL images into one.
    direction: 0(default) horizontal; 1:vertical
    '''
    assert direction in [0,1]
    if direction:
        im1 = im1.transpose(Image.Transpose.ROTATE_90)
        im2 = im2.transpose(Image.Transpose.ROTATE_90)
    w = im1.size[0] + im2.size[0]
    h = max(im1.size[1], im2.size[1])
    im = Image.new("RGBA", (w, h))

    im.paste(im1)
    im.paste(im2, (im1.size[0], 0))
    if direction:
        im = im.transpose(Image.Transpose.ROTATE_270)
    return im

def sym_image(image:ImageFile, dir:SymDir = SymDir.LEFT_TO_RIGHT):
    x_size, y_size = image.size
    
    match dir:
        case SymDir.LEFT_TO_RIGHT:
            box = (0,0,x_size//2,y_size)
            half = image.crop(box)
            flip_img = half.transpose(Image.FLIP_LEFT_RIGHT)
            im = merge(half,flip_img)
            #im.save(filepath)
            return im

        case SymDir.RIGHT_TO_LEFT:
            box = (x_size//2,0,x_size,y_size)
            half = image.crop(box)
            flip_img = half.transpose(Image.FLIP_LEFT_RIGHT)
            im = merge(flip_img,half)
            #im.save(filepath)
            return im

        case SymDir.UP_TO_DOWN:
            box = (0,0,x_size,y_size//2)
            half = image.crop(box)
            flip_img = half.transpose(Image.FLIP_TOP_BOTTOM)
            im = merge(half,flip_img,1)
            #im.save(filepath)
            return im

        case SymDir.DOWN_TO_UP:
            box = (0,y_size//2,x_size,y_size)
            half = image.crop(box)
            flip_img = half.transpose(Image.FLIP_TOP_BOTTOM)
            im = merge(flip_img,half,1)
            #im.save(filepath)
            return im
            


def sticker_filter(message:Message):
   
    for item in message.content:
        if item.type == 'image':
            print(message)
            image = dl_image(item.data.url,'data/tmp.jpg')
            return image
    return None


#暂定是根据回复消息里第一个词为对称
class SymModule(Module):
    prerequisite = ['config','archive']
    def __init__(self):
        self.config = None
        self.recent_messages = None
        self.logger = logger.Logger()
        self.archive = None
    def register(self, message_handler, event_handler, mod):
        message_handler.register_listener(self, EventType.EVENT_RECV_MSG, self.on_recv_msg)
        self.config = mod.config
        self.archive = mod.archive
        self.config.register_config('sym_image', module=self)
        

    async def on_recv_msg(self, event : Event, context : EventContext):
        message = event.data
        config = context.mod.config
        message_handler = context.message_handler
        if not config.sym_image or not isinstance(event.data, Message):
            return False
        
        is_sym = 0
        reply_id = 0
        self.logger.debug(message.content)
        for piece in message.content:
            if piece.type == 'text' and '对称' in str(piece):
                is_sym+=1
            if piece.type == 'reply':
                reply_id = int(piece.data)
        if is_sym and reply_id:
            target_message = self.archive.chat_history_manager.find_message_by_message_id(reply_id)
            self.logger.debug(target_message.message)
            image = sticker_filter(target_message.message)
            if image is not None:
                im = sym_image(image)
                
                im.save('test.png')
                im_base64 = get_base64(im.tobytes())
                await message_handler.send_message(Message([MessageComponent('image', im_base64)]))
                


            





async def connect():
        """连接WebSocket并处理消息"""
        while True:
            try:
                async with websockets.connect(
                    "ws://127.0.0.1:3001/",
                    ping_interval=60,
                    ping_timeout=30,
                    close_timeout=10
                ) as ws:
                    logg.debug("Napcat WebSocket 已连接")


                    logg.debug("模块初始化完成")
                    
                    logg.debug("消息处理器已启动")
                    
                    logg.debug("Autowater 启动完成。")
                    # 运行消息处理
                    async for message in ws:
                        message = json.loads(message)
                        #print(message)
                        sticker_filter(message)
                    break
            except Exception as e:
                if logger.debug_flag:
                    raise e

                logg.error(f"WebSocket连接错误: {e}，正在尝试重新连接...")
                await asyncio.sleep(5)
                continue

if __name__ == '__main__':
    #asyncio.run(connect())
    sym_image(Image.open('data/951275C6838D8A0E4B36496F978F46DF.png'),'data/test.png',dir=SymDir.DOWN_TO_UP)