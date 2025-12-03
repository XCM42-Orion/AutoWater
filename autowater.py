import asyncio
from config import Config
from websocket_client import WebSocketClient

async def main():
    # 加载配置
    config = Config("config.json")
    
    # 创建WebSocket客户端
    client = WebSocketClient(config)
    
    # 连接并运行
    print("Autowater已启动，正在连接WebSocket...")
    try:
        await client.connect()
    except KeyboardInterrupt:
        print("程序已停止")

if __name__ == "__main__":
    asyncio.run(main())