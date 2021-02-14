import json

from django.contrib.auth import get_user_model

from channels.generic.websocket import AsyncJsonWebsocketConsumer


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
        if command == "send":
            if len(content['message'].lstrip()) == 0:
                raise Exception("无法发送空白消息")
            await self.send_message(content['message'])

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
        await self.send_json({
                "profile_image": event["profile_image"],
                "username": event["username"],
                "user_id": event["user_id"],
                "message": event["message"],
            },
        )
