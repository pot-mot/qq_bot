import json
import uuid


class TextMessage:
    text: str


class UserTextMessage(TextMessage):
    user_id: int

    def __init__(self, user_id: int, text: str) -> None:
        self.user_id = user_id
        self.text = text


class GroupTextMessage(TextMessage):
    group_id: int

    def __init__(self, group_id: int, text: str) -> None:
        self.group_id = group_id
        self.text = text


async def send_message(websocket, message: TextMessage):
    echo = str(uuid.uuid4())
    if isinstance(message, UserTextMessage):
        await websocket.send(json.dumps({
            "action": "send_private_msg",
            "params": {
                "user_id": message.user_id,
                "message": {
                    "type": "text",
                    "data": {
                        "text": message.text
                    }
                }
            },
            'echo': echo
        }))
    elif isinstance(message, GroupTextMessage):
        await websocket.send(json.dumps({
            "action": "send_group_msg",
            "params": {
                "group_id": message.group_id,
                "message": {
                    "type": "text",
                    "data": {
                        "text": message.text
                    }
                }
            },
            'echo': echo
        }))
