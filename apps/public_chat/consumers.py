import json
from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.humanize.templatetags.humanize import naturalday, naturaltime
from django.utils import timezone

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from public_chat.models import PublicChatroom

MSG_TYPE_MESSAGE = 0  # 正常消息

User = get_user_model()


class PublicChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        """
        Called when websocket is handshaking as part of initial connection
        """
        print("PublicChatConsumer: connect:" + str(self.scope['user']))
        await self.accept()

        self.room_id = None

    async def disconnect(self, code):
        """
        Called when a WebSocket connection is closed.
        """
        print("PublicChatConsumer disconnect")
        try:
            if self.room_id is not None:
                await self.leave_room(self.room_id)
        except Exception:
            pass

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
                await self.send_room(content["room_id"], content['message'])
            elif command == "join":
                # Make them join the room
                await self.join_room(content["room_id"])
            elif command == "leave":
                # Leave the room
                await self.leave_room(content["room_id"])
        except ClientError as e:
            await self.handle_client_error(e)

    async def send_room(self, room_id, message):
        """
        Called by receive_json when someone sends a message to a room.
        """
        # Check they are in this room
        print("PublicChatConsumer: send_room")
        if self.room_id is not None:
            if str(room_id) != str(self.room_id):
                raise ClientError("ROOM_ACCESS_DENIED", "Room access denied")
            if not is_authenticated(self.scope["user"]):
                raise ClientError("AUTH_ERROR", "You must be authenticated to chat.")
        else:
            raise ClientError("ROOM_ACCESS_DENIED", "Room access denied")

        # Get the room and send to the group about it
        room = await get_room_or_error(room_id)

        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.message",
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

    async def join_room(self, room_id):
        """
        Called by receive_json when someone sent a join command.
        """
        print("PublicChatConsumer: join_room")
        is_auth = is_authenticated(self.scope["user"])
        try:
            room = await get_room_or_error(room_id)
        except ClientError as e:
            await self.handle_client_error(e)
        else:
            # Add user to "users" list for room
            if is_auth:
                await connect_user(room, self.scope["user"])

            # Store that we're in the room
            self.room_id = room.id

            # Add them to the group so they get room messages
            await self.channel_layer.group_add(
                room.group_name,
                self.channel_name,
            )

            # Instruct their client to finish opening the room
            await self.send_json({
                "join": str(room.id)
            })

    async def leave_room(self, room_id):
        """
        Called by receive_json when someone sent a leave command.
        """
        print("PublicChatConsumer: leave_room")
        is_auth = is_authenticated(self.scope["user"])
        room = await get_room_or_error(room_id)

        # Remove user from "users" list
        if is_auth:
            await disconnect_user(room, self.scope["user"])

        # Remove that we're in the room
        self.room_id = None
        # Remove them from the group so they no longer get room messages
        await self.channel_layer.group_discard(
            room.group_name,
            self.channel_name,
        )

    async def handle_client_error(self, e):
        """
        Called when a ClientError is raised.
        Sends error data to UI.
        """
        errorData = {'error': e.code}
        if e.message:
            errorData['message'] = e.message
            await self.send_json(errorData)


def is_authenticated(user):
    return user.is_authenticated


@database_sync_to_async
def connect_user(room, user):
    return room.connect_user(user)


@database_sync_to_async
def disconnect_user(room, user):
    return room.disconnect_user(user)


@database_sync_to_async
def get_room_or_error(room_id):
    """
    Tries to fetch a room for the user
    """
    try:
        room = PublicChatroom.objects.get(pk=room_id)
    except PublicChatroom.DoesNotExist:
        raise ClientError("ROOM_INVALID", "房间不存在")
    return room


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
