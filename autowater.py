import asyncio
from config import Config
from websocket_client import WebSocketClient

async def main():
    # 加载配置
    config = Config("config.json")
    
    # 创建WebSocket客户端
    client = WebSocketClient(config)
    
    # 连接并运行
    try:
        await client.connect()
    except KeyboardInterrupt:
        print("程序已停止")
    except Exception as e:
        print(f"程序运行出错: {e}")

if __name__ == "__main__":
    asyncio.run(main())