import random
import uuid
import asyncio
import json
import websockets
from typing import List
from DiceInfixCalculator import DiceInfixCalculator, DiceRollInfo


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
                    if message_text.lstrip().startswith(('.', '。')):
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


diceInfixCalculator = DiceInfixCalculator()


def generate_result(raw_message: str, sender_id: str, sender_nickname: str) -> str:
    stripped_message = raw_message.strip()
    if not stripped_message.startswith(('.', '。')):
        return ""

    # 去掉开头的 . 或 。
    command = stripped_message[1:].strip()

    if command == "":
        return "请输入有效的指令"

    if command == "help":
        return "支持的指令: \n.help\n.info\n.pot\n.mot\n.r\n.rd数字\n.r数字d数字"

    if command.startswith("pot"):
        return f"{sender_nickname} 获得了 {random.randint(1, 6)} 个土豆"
    if command.startswith("mot"):
        return f"{sender_nickname} 获得了 {random.randint(1, 100)} db 的尖叫"
    if command == "info":
        return "自律型外星追车油炸土拨鼠鸡蛋土豆饼bot by potmot(377029227)\n纯正则匹配，无协议无核心（"

    # 计算骰子表达式
    if command.startswith("r"):
        try:
            expression = command[1:].strip().replace(" ", "").lower()
            if len(expression) == 0:
                expression = "d100"
            dice_infos: List[DiceRollInfo] = []
            result = diceInfixCalculator.calculate(expression, dice_infos)
            dice_info_strs = [str(info) for info in dice_infos]
            dice_info_str = \
                f"\n[\n{',\n'.join(dice_info_strs)}\n]"
            return f"{sender_nickname} 掷出了 {result}{dice_info_str}" if (
                    len(dice_infos) > 0
            ) else f"{sender_nickname} 计算得到 {result}"
        except ValueError as e:
            return f"错误: {str(e)}"
        except Exception as e:
            return f"未知错误: {str(e)}"

    # 未知指令
    return f"未知指令: {command}\n支持的指令: .r .rd"


async def main():
    uri = "ws://localhost:3001"

    async with websockets.connect(uri) as websocket:
        asyncio.create_task(receive_messages(websocket))
        while True:
            await async_input("输入消息内容: ")
        #     await send_message_to_group(websocket, group_id, message)


if __name__ == "__main__":
    asyncio.run(main())
