import random
import re
import uuid
import asyncio
import json

import websockets


async def async_input(prompt: str = "") -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)


async def send_message_to_user(websocket, user_id: str, message: str):
    data = {
        "action": "send_private_msg",
        "params": {
            "user_id": user_id,
            "message": {
                "type": "text",
                "data": {
                    "text": message
                }
            }
        },
        'echo': str(uuid.uuid4())
    }
    await websocket.send(json.dumps(data))


async def send_message_to_group(websocket, group_id: str, message: str):
    data = {
        "action": "send_group_msg",
        "params": {
            "group_id": group_id,
            "message": {
                "type": "text",
                "data": {
                    "text": message
                }
            }
        },
        'echo': str(uuid.uuid4())
    }
    await websocket.send(json.dumps(data))


async def receive_messages(ws):
    while True:
        try:
            message = await ws.recv()
            message_dict = json.loads(message)

            if "self_id" not in message_dict:
                continue

            self_id = message_dict["self_id"]
            if "sender" in message_dict and "message" in message_dict:
                sender = message_dict["sender"]
                if "user_id" not in sender or "nickname" not in sender:
                    continue

                sender_id = sender["user_id"]
                if self_id == sender_id:
                    continue

                print(f"收到消息: {message_dict}")

                sender_nickname = sender["nickname"]
                messages = message_dict["message"]

                if type(messages) != list:
                    continue

                for message in messages:
                    if "type" not in message:
                        continue
                    message_type = message["type"]

                    # 仅处理文本消息
                    if message_type != "text":
                        continue

                    if "data" not in message:
                        continue
                    message_data = message["data"]
                    if "text" not in message_data:
                        continue

                    message_text: str = message_data["text"]
                    if message_text.lstrip().startswith("."):
                        result: str = generate_result(message_text, sender_id, sender_nickname)
                        if "group_id" in message_dict:
                            group_id: str = message_dict["group_id"]
                            await send_message_to_group(ws, group_id, result)
                        else:
                            await send_message_to_user(ws, sender_id, result)

        except websockets.exceptions.ConnectionClosed:
            print("WebSocket 连接已关闭")
            break
        except json.JSONDecodeError:
            print("接收到无效的 JSON 数据")
        except Exception as e:
            print(f"发生未知错误: {e}")


def generate_result(raw_message: str, sender_id: str, sender_nickname: str) -> str:
    stripped_message = raw_message.strip()
    if not stripped_message.startswith(('.', '。')):
        return ""

    # 去掉开头的 . 或 。
    command = stripped_message[1:].strip()

    if command == "":
        return "请输入有效的指令"

    # r 指令 - 生成 1-100 的随机数
    if command == "r":
        return f"{sender_nickname} 投掷1D100: {random.randint(1, 100)}"

    if command == "help":
        return "支持的指令: .r, .rd数字, .r数字d数字"

    # rd(Number) 指令 - 生成 1 到指定数字的随机数
    rd_match = re.match(r"^rd(\d+)$", command)
    if rd_match:
        max_value = int(rd_match.group(1))
        if max_value <= 0:
            return "错误：数字必须大于0"
        return f"{sender_nickname} 投掷1D{max_value}: {random.randint(1, max_value)}"

    # r(Number)d(Number) 指令 - 生成多个指定范围的随机数
    rdd_match = re.match(r"^r(\d+)d(\d+)$", command)
    if rdd_match:
        count = int(rdd_match.group(1))
        max_value = int(rdd_match.group(2))

        if count <= 0 or max_value <= 0:
            return "错误：数字必须大于0"

        results = [str(random.randint(1, max_value)) for _ in range(count)]
        total = sum(int(x) for x in results)
        return f"{sender_nickname} 投掷{count}D{max_value}: {', '.join(results)} (总计: {total})"

    # 未知指令
    return f"未知指令: {command}\n支持的指令: .r, .rd数字, .r数字d数字"


async def main():
    uri = "ws://localhost:3001"

    async with websockets.connect(uri) as websocket:
        asyncio.create_task(receive_messages(websocket))
        while True:
            await async_input("输入消息内容: ")
        #     await send_message_to_group(websocket, group_id, message)


asyncio.run(main())