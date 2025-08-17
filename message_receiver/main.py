import atexit
import json
import random
import asyncio
import time
from logging.handlers import TimedRotatingFileHandler
import re
import websockets
import logging
import signal
from typing import List
from dice import calculate as calculate_dice_expression, DiceRollInfo
from message import TextMessage, send_message, GroupTextMessage, UserTextMessage
from skill import pass_skill_value_expression, calculate_skill_roll_expression, SkillRollResult
from user import UserInfoStore, UserInfo, CharacterInfo

# 全局用户信息缓存实例
user_infos = UserInfoStore()

# 用于标识是否已执行清理
cleanup_done = False


def cleanup():
    global cleanup_done
    if not cleanup_done:
        logging.info("执行清理操作...")
        user_infos.stop()
        cleanup_done = True


# 信号处理函数
def signal_handler(signum, frame):
    logging.info(f"收到信号 {signum}，准备退出...")
    cleanup()
    # 退出程序
    import sys
    sys.exit(0)


atexit.register(cleanup)


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

                logging.info(f"收到消息: {message_dict}")

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
                                        result: TextMessage = (
                                            execute_command(actual_command, sender_id, sender_nickname, group_id)
                                        )
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
            logging.info("WebSocket 连接已关闭")
            break
        except json.JSONDecodeError:
            logging.error("接收到无效的 JSON 数据")
        except Exception as e:
            logging.error(f"发生未知错误: {e}")


def execute_command(command: str, sender_id: int, sender_nickname: str, group_id: int or None = None) -> TextMessage:
    # 记录执行的命令
    logging.info(f"用户 {sender_nickname}({sender_id}) 执行命令: {command}")

    def to_user_message(message: str) -> UserTextMessage:
        return UserTextMessage(sender_id, message)

    def to_text_message(message: str) -> TextMessage:
        if group_id is not None:
            return GroupTextMessage(group_id, message)
        else:
            return UserTextMessage(sender_id, message)

    def calculate_dice_expression_message(expression: str) -> str:
        try:
            if len(expression) == 0:
                expression = "d"
            dice_infos: List[DiceRollInfo] = []
            result = calculate_dice_expression(expression, dice_infos)
            dice_info_strs = [str(info) for info in dice_infos]
            dice_info_strs_join = "\n".join(dice_info_strs)
            dice_info_str = f"[\n{dice_info_strs_join}\n]"
            return f"{sender_nickname} 掷出了 {result}{dice_info_str}" if (
                        len(dice_infos) > 0
                ) else f"{sender_nickname} 计算得到 {result}"
        except ValueError as e:
            return f"值错误: {str(e)}"
        except Exception as e:
            return f"未知错误: {str(e)}"

    def roll_skill(expression: str, current_character: CharacterInfo or None) -> str:
        if current_character is None:
            current_user.set_current_character(sender_nickname)
            current_character = current_user.get_current_character_info()
        result: SkillRollResult = calculate_skill_roll_expression(expression, current_character)
        return f"{current_character.name} 投掷技能 {result.skill_name} ({result.roll_result}/{result.skill_value})，${result.success_type}~"

    # 获取当前日期的时间戳（当天0点的时间戳）
    current_date = time.localtime()
    today_start = time.mktime((current_date.tm_year, current_date.tm_mon, current_date.tm_mday, 0, 0, 0, 0, 0, 0))
    today_start_ns = int(today_start * 1_000_000_000)  # 转换为纳秒

    current_user: UserInfo = user_infos.get_user(sender_id, sender_nickname)
    current_character: CharacterInfo or None = None
    if current_user.current_character_name is not None:
        current_character = current_user.get_current_character_info()

    lower_command = command.lower()
    if lower_command == "info":
        return to_text_message(
            "自律型外星追车油炸土拨鼠鸡蛋土豆饼bot by potmot(377029227)\n纯文本指令匹配，无协议无核心（")

    if lower_command == "help":
        return to_text_message("支持的指令: \n.help\n.info\n.pot\n.pot show\n.mot\n.pc new\n.pc list\n.st\n.pc del\n.nn\n.r\n.rd\n.ra\n")

    if lower_command.startswith("pot"):
        if re.match(r"pot\s+show", lower_command):
            return to_text_message(f"{sender_nickname} 现在有 {current_user.points} 个土豆")

        if current_user.last_point_get_time > today_start_ns:
            return to_text_message("今日份土豆已发放~")

        potato_count: int = random.randint(1, 6)
        if potato_count == 1:
            if random.randint(1, 100) == 100:
                potato_count = 100
        current_user.increase_points(potato_count)
        current_user.last_point_get_time = time.time_ns()
        return to_text_message(f"{sender_nickname} 获得了 {potato_count} 个土豆")

    if lower_command == "mot":
        voice_force = random.randint(1, 240)
        return to_text_message(f"{sender_nickname} 触碰土拨鼠，土拨鼠发出了 {voice_force} db 的尖叫")

    if lower_command == "jrrp":
        if current_user.last_lucky_point_check_time < today_start_ns:
            current_user.lucky_points = random.randint(1, 100)
            current_user.last_lucky_point_check_time = time.time_ns()
        return to_text_message(f"{sender_nickname} 今日人品为 {current_user.lucky_points}")

    # 角色部分
    if lower_command.startswith("pc"):
        expression = command[2:].strip()
        if expression.lower().startswith("new"):
            name = expression[3:].strip()
            if name == "":
                return to_text_message(f"{sender_nickname} 角色名称不能为空")
            current_user.set_current_character(name)
            return to_text_message(f"{sender_nickname} 创建了角色 {name}")
        if expression.lower().startswith("list"):
            character_names = "\n".join(list(current_user.characters.keys()))
            return to_text_message(f"{sender_nickname} 的角色列表: \n{character_names}")
        if expression.lower().startswith("del"):
            name = expression[3:].strip()
            if name == "":
                return to_text_message(f"{sender_nickname} 角色名称不能为空")
            if name in current_user.characters:
                current_user.remove_character(name)
                return to_text_message(f"{sender_nickname} 删除了角色 {name}")
            else:
                return to_text_message(f"{sender_nickname} 不存在角色 {name}")
    # 名称部分
    if lower_command.startswith("nn"):
        name = command[2:].strip()
        if name == "":
            return to_text_message(f"{sender_nickname} 角色名称不能为空")
        if current_character is None:
            current_user.set_current_character(name)
            return to_text_message(f"{sender_nickname} 创建了角色 {name}")
        else:
            current_character.name = name
            return to_text_message(f"{sender_nickname} 设置角色名称为 {name}")

    # 设置技能
    if lower_command.startswith("st"):
        expression = command[2:].strip().replace(" ", "")
        skill_values = pass_skill_value_expression(expression)
        if current_character is None:
            current_user.set_current_character(sender_nickname)
            current_character = current_user.get_current_character_info()
        for skill_name, value in skill_values.items():
            current_character.set_skill_value(skill_name, value)

    # 投掷技能
    if lower_command.startswith("rah"):
        expression = command[2:].strip().replace(" ", "")
        return to_user_message(roll_skill(expression, current_character))
    if lower_command.startswith("ra"):
        expression = command[3:].strip().replace(" ", "")
        return to_text_message(roll_skill(expression, current_character))

    # 投掷普通骰子
    if lower_command.startswith("rh"):
        expression = lower_command[2:].strip().replace(" ", "")
        return to_user_message(calculate_dice_expression_message(expression))
    if lower_command.startswith("r"):
        expression = lower_command[1:].strip().replace(" ", "")
        return to_text_message(calculate_dice_expression_message(expression))

    # 未知指令
    return to_text_message(f"未知指令: {command}\n支持的指令请执行.help")


async def main():
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    log_format = "%(asctime)s - %(levelname)s - %(message)s"

    logging.basicConfig(level=logging.INFO, format=log_format)

    # 创建一个按天轮转的日志处理器，保留所有日志
    timed_handler = TimedRotatingFileHandler(
        filename='bot.log',
        when='midnight',
        interval=1,
        backupCount=0,  # 设置为0表示不删除旧日志文件
        encoding='utf-8'
    )
    timed_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(timed_handler)

    uri = "ws://localhost:3001"

    try:
        async with websockets.connect(uri) as websocket:
            logging.info(f"已连接到WebSocket服务器: {uri}")
            await asyncio.create_task(receive_messages(websocket))
            stop_event = asyncio.Event()
            await stop_event.wait()  # 永远等待
    except Exception as e:
        logging.error(f"WebSocket连接失败: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        cleanup()
