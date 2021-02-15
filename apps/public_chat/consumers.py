import json
from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.humanize.templatetags.humanize import naturalday, naturaltime
from django.utils import timezone

from channels.generic.websocket import AsyncJsonWebsocketConsumer

MSG_TYPE_MESSAGE = 0  # 正常消息

User = get_user_model()


class PublicChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        """
        Called when websocket is handshaking as part of initial connection
        """
        print("PublicChatConsumer: connect:" + str(self.scope['user']))
        await self.accept()

        # 将用户加入 group
        await self.channel_layer.group_add(
            "public_chatroom_1",
            self.channel_name
        )

    async def disconnect(self, code):
        """
        Called when a WebSocket connection is closed.
        """
        print("PublicChatConsumer disconnect")

    async def receive_json(self, content, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload for us and pass it as the first argument.
        """
        command = content.get("command", None)
        message = content.get("message", None)
        print(f"PublicChatConsumer: receive_json: command: {command}, message: {message}")
        try:
            if command == "send":
                if len(content['message'].lstrip()) == 0:
                    raise ClientError(422, "无法发送空白消息")  # HTTP 状态码422 Unprocessable Entity
                await self.send_message(content['message'])
        except ClientError as e:
            errorData = {'error': e.code}

            if e.message:
                errorData['message'] = e.message
            await self.send_json(errorData)

    async def send_message(self, message):
        await self.channel_layer.group_send(
            "public_chatroom_1",
            {
                "type": "chat.message",  # chat_message
                "profile_image": self.scope["user"].profile_image.url,
                "username": self.scope["user"].username,
                "user_id": self.scope["user"].id,
                "message": message,
            }
        )

    async def chat_message(self, event):
        """
        Called when someone has messaged our chat.
        将
        """
        # Send a message down to the client
        print("PublicChatConsumer: chat_message from user #" + str(event["user_id"]))
        timestamp = calculate_timestamp(timezone.now())
        await self.send_json({
                "msg_type": MSG_TYPE_MESSAGE,
                "profile_image": event["profile_image"],
                "username": event["username"],
                "user_id": event["user_id"],
                "message": event["message"],
                "natural_timestamp": timestamp,
            },
        )


class ClientError(Exception):
    """

    """
    def __init__(self, code, message):
        super().__init__(code)
        self.code = code
        if message:
            self.message = message


def calculate_timestamp(timestamp):
    """

    """
    # today or yesterday
    if (naturalday(timestamp) == "today") or (naturalday(timestamp) == "yesterday"):
        str_time = datetime.strftime(timestamp, "%I:%M %p")
        str_time = str_time.strip("0")
        ts = f"{naturalday(timestamp)} at {str_time}"
    # other days
    else:
        str_time = datetime.strftime(timestamp, "%m/%d/%Y")
        ts = f"{str_time}"
    return str(ts)
