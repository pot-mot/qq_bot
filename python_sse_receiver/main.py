import json
import random
import asyncio
import websockets
from typing import List
from DiceInfixCalculator import DiceInfixCalculator, DiceRollInfo
from message import TextMessage, send_message, GroupTextMessage, UserTextMessage


async def async_input(prompt: str = "") -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)


async def receive_messages(ws):
    while True:
        try:
            message = await ws.recv()
            message_dict = json.loads(message)

            if "self_id" not in message_dict:
                continue

            self_id: int = message_dict["self_id"]
            group_id: int or None = None
            if "group_id" in message_dict:
                group_id = message_dict["group_id"]

            if "sender" in message_dict and "message" in message_dict:
                sender = message_dict["sender"]
                if "user_id" not in sender or "nickname" not in sender:
                    continue

                sender_id: int = sender["user_id"]
                if self_id == sender_id:
                    continue

                print(f"收到消息: {message_dict}")

                sender_nickname = sender["nickname"]
                messages = message_dict["message"]

                if not isinstance(messages, list):
                    continue

                has_at = False
                at_self = False
                message_results: list[TextMessage] = []

                for message in messages:
                    if "type" not in message:
                        continue
                    message_type = message["type"]

                    # 处理文本消息
                    if message_type == "text":
                        if "data" not in message:
                            continue
                        message_data = message["data"]
                        if "text" not in message_data:
                            continue

                        message_text: str = message_data["text"]
                        stripped_message = message_text.lstrip()
                        if stripped_message.startswith(('.', '。')):
                            command = stripped_message.strip()
                            if len(command) == 1:
                                continue
                            commands = command.split('\n')
                            for single_command in commands:
                                single_command = single_command.strip()
                                # 检查每行是否以 . 或 。 开头
                                if single_command.startswith(('.', '。')):
                                    # 如果是，则去掉前缀并执行命令
                                    actual_command = single_command[1:].strip()
                                    if len(actual_command) > 0:  # 忽略空行
                                        result: TextMessage = execute_command(actual_command, sender_id, sender_nickname, group_id)
                                        message_results.append(result)

                    elif message_type == "at":
                        has_at = True
                        if "data" not in message:
                            continue

                        message_data = message["data"]
                        if "qq" in message_data:
                            at_qq: str = message_data["qq"]
                            if at_qq == str(self_id) or at_qq == "all":
                                at_self = True

                if (
                        has_at and at_self
                ) or (
                        not has_at
                ):
                    for result in message_results:
                        await send_message(ws, result)

        except websockets.exceptions.ConnectionClosed:
            print("WebSocket 连接已关闭")
            break
        except json.JSONDecodeError:
            print("接收到无效的 JSON 数据")
        except Exception as e:
            print(f"发生未知错误: {e}")


diceInfixCalculator = DiceInfixCalculator()


def execute_command(command: str, sender_id: int, sender_nickname: str, group_id: int or None = None) -> TextMessage:
    def to_text_message(message: str) -> TextMessage:
        if group_id is not None:
            return GroupTextMessage(group_id, message)
        else:
            return UserTextMessage(sender_id, message)

    if command == "info":
        return to_text_message(
            "自律型外星追车油炸土拨鼠鸡蛋土豆饼bot by potmot(377029227)\n纯文本指令匹配，无协议无核心（")

    if command == "help":
        return to_text_message("支持的指令: \n.help\n.info\n.pot\n.mot\n.r\n.rd数字\n.r数字d数字")

    if command == "pot":
        potato_count: int = random.randint(1, 6)
        if potato_count == 1:
            if random.randint(1, 100) == 100:
                potato_count = 100
        return to_text_message(f"{sender_nickname} 获得了 {potato_count} 个土豆")

    if command == "mot":
        voice_force = random.randint(1, 240)
        return to_text_message(f"{sender_nickname} 触碰土拨鼠，土拨鼠发出了 {voice_force} db 的尖叫")

    # 计算骰子表达式
    if command.startswith("r"):
        try:
            expression = command[1:].strip().replace(" ", "").lower()
            if len(expression) == 0:
                expression = "d100"
            dice_infos: List[DiceRollInfo] = []
            result = diceInfixCalculator.calculate(expression, dice_infos)
            dice_info_strs = [str(info) for info in dice_infos]
            dice_info_strs_join = "\n".join(dice_info_strs)
            dice_info_str = f"[\n{dice_info_strs_join}\n]"
            return to_text_message(
                f"{sender_nickname} 掷出了 {result}{dice_info_str}" if (
                        len(dice_infos) > 0
                ) else f"{sender_nickname} 计算得到 {result}"
            )
        except ValueError as e:
            return to_text_message(f"值错误: {str(e)}")
        except Exception as e:
            return to_text_message(f"未知错误: {str(e)}")

    # 未知指令
    return to_text_message(f"未知指令: {command}\n支持的指令请执行.help")


async def main():
    uri = "ws://localhost:3001"

    async with websockets.connect(uri) as websocket:
        await asyncio.create_task(receive_messages(websocket))
        stop_event = asyncio.Event()
        await stop_event.wait()  # 永远等待
        # while True:
        #     await async_input("输入消息内容: ")
        #     await send_message_to_group(websocket, group_id, message)


if __name__ == "__main__":
    asyncio.run(main())
