import asyncio
import json
import websockets
import random
from datetime import datetime,time

with open ("config.json","r",encoding='utf-8') as jsonload:
    config = json.load(jsonload)

NAPCAT_WS_URL = config.get('napcat_url')     # ← 改成你的 NapCat WS 地址
TARGET_GROUP = config.get('target_groups') # ← 在config里填你的目标群
SET_EMOJI =  config.get('set_emoji')
SET_REPLY = config.get('set_reply')
KEYWORD_REPLY = config.get('keyword_reply')
KEYWORD_POSSI = config.get('keyword_possibility')             
REPLY_TEXT = config.get('random_reply')      # ← 回复内容
AT_REPLY = config.get('ated_reply')
TIME_REPLY = config.get('time_reply')
key_possi = config.get('keyword_possibility')
set_possi = config.get("set_reply_possiblity")
emo_possi = config.get("emoji_possibility")
rand_possi = config.get("random_reply_possibility")
repeat_possi = config.get("repeat_possibility")
at_possi = config.get("at_possibility")
ated_possi = config.get("ated_reply_possibility")
poke_possi = config.get("poke_possibility")
do_report = config.get("do_report")


async def message(ws):
        text = ""
        repeat_num = 0
        while True:
            raw = await ws.recv()
            data = json.loads(raw)
            text_last = text
            # -----------------------------
            # 只处理群消息
            # -----------------------------
            if data.get("post_type") == "message" and data.get("message_type") == "group":
                group_id = data["group_id"]
                if group_id in TARGET_GROUP:
                    text = data.get("raw_message") or data.get("message")
                    is_reply = False
                    is_keyword = False
                    is_repeat = False

                    # 复读
                    if text == text_last:
                        repeat_num += 1
                        randomnum = random.random()
                        if randomnum <= repeat_possi and repeat_num == 1:
                            payload = {
                                        "action": "send_group_msg",
                                        "params": {
                                            "group_id": group_id,
                                            "message": text
                                        }
                                    }
                            await asyncio.sleep(0.2)
                            await ws.send(json.dumps(payload))
                            print(f"收到复读消息:{text}")
                            print(f"已向群 {group_id} 回复：{text}")
                            is_repeat = True
                    if is_repeat == True:
                        continue
                    if text != text_last:
                        repeat_num = 0

                    # 被艾特回复
                    msg = data.get("message", [])
                    self_id = str(data.get("self_id"))

                    if any(seg.get("type") == "at" and seg["data"].get("qq") == self_id for seg in msg):
                        randomnum = random.random()
                        if randomnum <= ated_possi:
                            reply = random.choice(AT_REPLY)
                            payload = {
                                "action":"send_group_msg",
                                "params":{
                                    "group_id":group_id,
                                    "message":reply
                                }
                            }
                            await asyncio.sleep(len(reply)+1)
                            await ws.send(json.dumps(payload))
                            print(f"已被{data.get("user_id")}艾特并回复{reply}")
                            continue

                    # 关键词回复
                    if KEYWORD_REPLY:
                        randomnum = random.random()
                        if randomnum <= key_possi:
                            for x in KEYWORD_REPLY:
                                if x['keyword'] in text:
                                    reply = random.choice(x['reply'])
                                    payload = {
                                        "action": "send_group_msg",
                                        "params": {
                                            "group_id": group_id,
                                            "message": reply
                                        }
                                    }
                                    await asyncio.sleep(len(reply)+len(text)*1.5)
                                    await ws.send(json.dumps(payload))
                                    print(f"收到关键词事件：{x['keyword']} in {text}",)
                                    print(f"已向群 {group_id} 回复：{reply}")
                                    is_keyword = True
                    if is_keyword == True:
                            continue                                    

                    # 指定对象的特殊回复(by Hikari)
                    if SET_REPLY:
                        randomnum = random.random()
                        if randomnum <= set_possi:
                            for x in SET_REPLY:
                                if data['user_id'] == x['id']:
                                    payload = {
                                        "action": "send_group_msg",
                                        "params": {
                                                    "group_id": group_id,
                                                    "message": [
                                                        {
                                                            "type": "reply",
                                                            "data": {
                                                                "id": data.get("message_id")
                                                            }
                                                        },
                                                        {
                                                            "type": "text",
                                                            "data": {
                                                                "text": x['reply']
                                                            }
                                                        }
                                                    ]
                                                }
                                    }
                                    await asyncio.sleep(len(x['reply'])+len(text)*1.5)
                                    await ws.send(json.dumps(payload))
                                    print(f"已回复{data['user_id']}:{x['reply']}")
                                    is_reply = True
                                    break
                    if is_reply == True:
                        continue

                    # 贴表情
                    if SET_EMOJI:
                        randomnum = random.random()
                        if randomnum <= emo_possi:
                            for x in SET_EMOJI:
                                if data['user_id'] == x['id']:
                                    payload = {
                                            "action": "set_msg_emoji_like",
                                            "params": {
                                                "message_id": data['message_id'],
                                                "emoji_id": x['emoji_id']
                                            }
                                        }
                                    await asyncio.sleep(3)
                                    await ws.send(json.dumps(payload))
                                    print(f"已给{data['user_id']}贴表情{x['emoji_id']}")
                                    break

                    # 随机艾特
                    randomnum = random.random()
                    if randomnum <= at_possi:
                        payload = {
                            "action": "send_group_msg",
                            "params": {
                                "group_id": group_id,
                                "message": [
                                    {
                                        "type": "reply",
                                        "data": {
                                            "id": data.get("message_id")
                                        }
                                    },
                                    {
                                        "type":"at",
                                        "data":{
                                            "qq": str(data['user_id'])
                                        }
                                    }
                                    ]
                                    }
                                    }
                        await asyncio.sleep(3)
                        await ws.send(json.dumps(payload))
                        print(f"已随机艾特回复{data['user_id']}")
                    
                    # 戳一戳
                    randomnum = random.random()
                    if randomnum <= poke_possi:
                        payload = { 
                            "action": "send_poke",
                            "params": {
                                "user_id": data['user_id'],
                                "group_id": group_id
                            }
                        }
                        await asyncio.sleep(3)
                        await ws.send(json.dumps(payload))
                        print(f"已戳一戳{data['user_id']}")


                    # 其他情况下的随机回复
                    randomnum = random.random()
                    if randomnum <= rand_possi: # 随机回复的概率是0.15，可以调s
                        # 构造 OneBot API 请求
                            reply = random.choice(REPLY_TEXT)
                            payload = {
                                "action": "send_group_msg",
                                "params": {
                                    "group_id": group_id,
                                    "message": reply
                                }
                            }
                            await asyncio.sleep(len(reply)+len(text)*1.5)
                            await ws.send(json.dumps(payload))
                            print("收到事件：", data)
                            print(f"已向群 {group_id} 回复：{reply}")


#自动播报

async def report(ws):
    if do_report:
            while True:
                now_time = datetime.now()
                for data in TIME_REPLY:
                    replytime = time.fromisoformat(data.get('time'))
                    if replytime.hour == now_time.hour and replytime.minute == now_time.minute:
                        for x in TARGET_GROUP:
                            payload = {
                                "action": "send_group_msg",
                                "params":{
                                    "group_id":x,
                                    "message":data.get('reply')
                                }
                            }
                            await ws.send(json.dumps(payload))
                await asyncio.sleep(60)

async def main():
    async with websockets.connect(NAPCAT_WS_URL) as ws:
        print("Napcat WebSocket 已连接")
        await asyncio.gather(message(ws),report(ws))
# 启动
asyncio.run(main())