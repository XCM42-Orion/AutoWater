import asyncio
import json
from websocket_client import WebSocketClient


async def main():
    # 加载配置
    with open('config.json', "r", encoding='utf-8') as f:
            config = json.load(f)

    napcat_url = config.get('napcat_url')
    
    # 创建WebSocket客户端
    client = WebSocketClient(napcat_url)
    
    # 连接并运行
    print("Autowater已启动，正在连接WebSocket...")
    try:
        await client.connect()
    except KeyboardInterrupt:
        print("程序已停止")

if __name__ == "__main__":
    asyncio.run(main())