import asyncio
import json
import websockets
import random

NAPCAT_WS_URL = "ws://127.0.0.1:3001/"     # ← 改成你的 NapCat WS 地址
TARGET_GROUP = []                  # ← 填你的目标群
REPLY_TEXT = ["喵",'太强了','饱饱','🈷️','和我做','强强！？','我是区','麦若，，，','妈妈','何意味','和一位','区，，，']      # ← 回复内容

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

                if group_id in TARGET_GROUP:
                    randomnum = random.random()
                    if randomnum <= 0.15: # 随机回复的概率是0.15，可以调
                    # 构造 OneBot API 请求
                        reply = random.choice(REPLY_TEXT)
                        payload = {
                            "action": "send_group_msg",
                            "params": {
                                "group_id": group_id,
                                "message": reply
                            }
                        }
                        await ws.send(json.dumps(payload))
                        print("收到事件：", data)
                        print(f"已向群 {group_id} 回复：{reply}")

# 启动

asyncio.run(main())
