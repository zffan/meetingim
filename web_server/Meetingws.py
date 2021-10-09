import asyncio
import websockets

# 向服务器端认证，用户名密码通过才能退出循环
async def auth_system(websocket):
    while True:
        cred_text = input("please enter your username and password: ")
        await websocket.send(cred_text)
        response_str = await websocket.recv()
        if "congratulation" in response_str:
            return True

# 向服务器端发送认证后的消息
async def send_msg(websocket):
    while True:
        _text = input("please enter your context: ")
        if _text == "exit":
            print(f'you have enter "exit", goodbye')
            await websocket.close(reason="user exit")
            return False
        await websocket.send(_text)
        recv_text = await websocket.recv()
        print(f"{recv_text}")

# 客户端主逻辑
async def main_logic():
    async with websockets.connect('wss://meeting-test.migu.cn:7778/im/ws?roomId=767645428&userId=19900000001&exp=21358699&ctime=1626259129418&signature=778551218636c8a0003df0f5be02afcf77d9458af9440877180eaa0b347accca') as websocket:
        await auth_system(websocket)

        await send_msg(websocket)

asyncio.get_event_loop().run_until_complete(main_logic())