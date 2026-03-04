import json
import time
from PIL import Image,ImageFile, ImageSequence
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


def dl_image(url:str):
    '''give an url, return downloaded image'''
    dl_path = urlretrieve(url)[0]

    return Image.open(dl_path)
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
            image = dl_image(item.data.url)
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
        #should be dealt with in on_register
        #create necessary folders
        if not os.path.exists('data'):
            os.mkdir('data')
        if not os.path.exists('data/temp'):
            os.mkdir('data/temp')
        #clear cache(<1month)
        tmp_path = 'data/temp'
        file_list = os.listdir(tmp_path)
        for file in file_list:
            cur_path = os.path.join(tmp_path,file)
            if os.path.isfile(cur_path) and cur_path[-3:] in ['png','jpg','gif']: #TODO
                time_difference = (time.time()*1000-int(file[:-4]))/1000
                if time_difference > 30*86400:
                    os.remove(cur_path)
        

    async def on_recv_msg(self, event : Event, context : EventContext):
        message = event.data
        config = context.mod.config
        message_handler = context.message_handler
        if not config.sym_image or not isinstance(event.data, Message):
            return False
        
        is_sym = 0
        sym_dir = SymDir.LEFT_TO_RIGHT
        reply_id = 0
        self.logger.debug(message.content)
        for piece in message.content:
            piece_params = str(piece).split()
            if piece.type == 'text' and piece_params[0]=='对称':
                is_sym+=1
                print(piece_params)
                if len(piece_params)==1:
                    continue
                match piece_params[1]:
                    case '左':
                        sym_dir = SymDir.LEFT_TO_RIGHT
                    case '右':
                        sym_dir = SymDir.RIGHT_TO_LEFT
                    case '上':
                        sym_dir = SymDir.UP_TO_DOWN
                    case '下':
                        sym_dir = SymDir.DOWN_TO_UP
            if piece.type == 'reply':
                reply_id = int(piece.data)
        if is_sym and reply_id:
            target_message = self.archive.chat_history_manager.find_message_by_message_id(reply_id)
            self.logger.debug(target_message.message)
            image = sticker_filter(target_message.message)
            if image is not None:
                frames = []
                for frame in ImageSequence.Iterator(image):

                    frames.append(sym_image(frame,sym_dir))
                tmp_time = int(time.time() * 1000)
                if 'duration' in image.info:
                    frames[0].save(f'data/temp/{tmp_time}.gif',format='GIF',save_all=True,append_images = frames[1:],duration=image.info['duration'], disposal=2)
                else:
                    frames[0].save(f'data/temp/{tmp_time}.gif',save_all=True,append_images = frames[1:])
                

                await message_handler.send_message(Message([MessageComponent('image', f'{os.getcwd()}/data/temp/{tmp_time}.gif')]))
     