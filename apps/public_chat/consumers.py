import json

from django.contrib.auth import get_user_model

from channels.generic.websocket import AsyncJsonWebsocketConsumer


User = get_user_model()


class PublicChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        """
        Called when websocket is handshaking as part of initial connection
        Returns
        -------

        """
        print("PublicChatConsumer: connect:" + str(self.scope['user']))
        await self.accept()

    async def disconnect(self, code):
        """
        Called when a WebSocket connection is closed.
        Parameters
        ----------
        code

        Returns
        -------

        """
        print("PublicChatConsumer disconnect")

    async def receive_json(self, content, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload for us and pass it as the first argument.
        Parameters
        ----------
        content
        kwargs

        Returns
        -------

        """
        command = content.get("command", None)
        print("PublicChatConsumer: receive_json: " + str(command))
