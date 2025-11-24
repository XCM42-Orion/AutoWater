import asyncio
import json
import websockets
import random

with open ("config.json","r",encoding='utf-8') as jsonload:
    config = json.load(jsonload)

NAPCAT_WS_URL = config.get('napcat_url')     # ← 改成你的 NapCat WS 地址
TARGET_GROUP = config.get('target_groups') # ← 在config里填你的目标群
SET_EMOJI =  config.get('set_emoji')
SET_REPLY = config.get('set_reply')
KEYWORD_REPLY = config.get('keyword_reply')
KEYWORD_POSSI = config.get('keyword_possibility')             
REPLY_TEXT = config.get('random_reply')      # ← 回复内容
key_possi = config.get('keyword_possibility')
set_possi = config.get("set_reply_possiblity")
emo_possi = config.get("emoji_possibility")
rand_possi = config.get("random_reply_possibility")


async def main():
    async with websockets.connect(NAPCAT_WS_URL) as ws:
        print("已连接 NapCat WebSocket")

        while True:
            raw = await ws.recv()
            data = json.loads(raw)

            # -----------------------------
            # 只处理群消息
            # -----------------------------
            if data.get("post_type") == "message" and data.get("message_type") == "group":
                group_id = data["group_id"]
                text = data.get("raw_message") or data.get("message")
                is_emoji = False
                is_reply = False
                is_keyword = False
                if group_id in TARGET_GROUP:

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
                                    await asyncio.sleep(len(reply))
                                    await ws.send(json.dumps(payload))
                                    print(f"收到关键词事件：{x['keyword']} in {text}",)
                                    print(f"已向群 {group_id} 回复：{reply}")
                                    is_keyword = True
                    if is_keyword == True:
                            continue                                    

                    # 特殊人类的特殊回复(by Hikari)
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
                                                                "id": data['user_id']
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
                                    await asyncio.sleep(len(x['reply']))
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
                                    is_emoji = True
                                    break
                    if is_emoji == True:
                        continue

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
                            await asyncio.sleep(len(reply))
                            await ws.send(json.dumps(payload))
                            print("收到事件：", data)
                            print(f"已向群 {group_id} 回复：{reply}")

# 启动
asyncio.run(main())