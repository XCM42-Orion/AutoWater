import asyncio
import json
from websocket_client import WebSocketClient
from logger import Logger


async def main():
    logger = Logger()
    print("\033[34m=========================================\n \nAutowater v1.5.0 by THU DoEating Association\n \n=========================================\033[0m")
    # 加载配置
    with open('config.json', "r", encoding='utf-8') as f:
            config = json.load(f)

    napcat_url = config.get('napcat_url')
    
    # 创建WebSocket客户端

    client = WebSocketClient(napcat_url)
    
    # 连接并运行
    logger.debug("Autowater已启动，正在连接WebSocket...")
    try:
        await client.connect()
    except KeyboardInterrupt:
        Logger().error("程序已停止")

if __name__ == "__main__":
    asyncio.run(main())