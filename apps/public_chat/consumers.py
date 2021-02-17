import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.paginator import Paginator
from django.core.serializers.python import Serializer
from django.utils import timezone

from chat.exceptions import ClientError
from chat.utils import calculate_timestamp
from public_chat.models import PublicChatroom, PublicChatroomMessage
from .constants import MSG_TYPE_CONNECTED_USER_COUNT, MSG_TYPE_MESSAGE, DEFAULT_ROOM_CHAT_MESSAGE_PAGE_SIZE


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
            elif command == "get_room_chat_messages":
                await self.display_progress_bar(True)
                room = await get_room_or_error(content['room_id'])
                payload = await get_room_chat_messages(room, content['page_number'])
                if payload is not None:
                    payload = json.loads(payload)
                    await self.send_messages_payload(payload['messages'], payload['new_page_number'])
                else:
                    raise ClientError(204, "聊天记录获取错误.")
                await self.display_progress_bar(False)
        except ClientError as e:
            await self.display_progress_bar(False)
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

        await create_public_room_chat_message(room, self.scope['user'], message)

        await self.channel_layer.group_send(
            room.group_name, {
                "type": "chat.message",  # 调用函数chat_message()
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
        })

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

            num_connected_users = get_num_connected_users(room)
            await self.channel_layer.group_send(room.group_name, {
                "type": "connected.user.count",  # 调用函数connected_user_count()
                "connected_user_count": num_connected_users,
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

        num_connected_users = get_num_connected_users(room)
        await self.channel_layer.group_send(room.group_name, {
            "type": "connected.user.count",  # 调用函数connected_user_count()
            "connected_user_count": num_connected_users,
        })

    async def handle_client_error(self, e):
        """
        Called when a ClientError is raised.
        Sends error data to UI.
        """
        errorData = {'error': e.code}
        if e.message:
            errorData['message'] = e.message
            await self.send_json(errorData)

    async def send_messages_payload(self, messages, new_page_number):
        """
        按分页形式，加载之前的消息
        Parameters
        ----------
        messages: 消息
        new_page_number: 页号

        Returns
        -------

        """
        print("PublicChatConsumer: send_messages_payload. ")

        await self.send_json({
            "messages_payload": "messages_payload",
            "messages": messages,
            "new_page_number": new_page_number,
        })

    async def display_progress_bar(self, is_displayed):
        print("DISPLAY PROGRESS BAR: " + str(is_displayed))
        await self.send_json({
            "display_progress_bar": is_displayed
        })

    async def connected_user_count(self, event):
        """
        Called to send the number of connected users to the room.
        This number is displayed in the room so other users know how many users are connected to the chat.
        """
        # Send a message down to the client
        print("PublicChatConsumer: connected_user_count: count: " + str(event["connected_user_count"]))
        await self.send_json({
            "msg_type": MSG_TYPE_CONNECTED_USER_COUNT,
            "connected_user_count": event["connected_user_count"]
        })


def is_authenticated(user):
    return user.is_authenticated


def get_num_connected_users(room):
    if room.users:
        return len(room.users.all())
    return 0


@database_sync_to_async
def create_public_room_chat_message(room, user, message):
    return PublicChatroomMessage.objects.create(user=user, room=room, content=message)


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


@database_sync_to_async
def get_room_chat_messages(room, page_number):
    try:
        qs = PublicChatroomMessage.objects.by_room(room)
        p = Paginator(qs, DEFAULT_ROOM_CHAT_MESSAGE_PAGE_SIZE)

        payload = {}

        new_page_number = int(page_number)
        if new_page_number <= p.num_pages:
            new_page_number = new_page_number + 1
            s = LazyRoomChatMessageEncoder()
            payload['messages'] = s.serialize(p.page(page_number).object_list)
        else:
            payload['messages'] = "None"
        payload['new_page_number'] = new_page_number
        return json.dumps(payload)

    except Exception as e:
        print("EXCEPTION: " + str(e))
        return None


class LazyRoomChatMessageEncoder(Serializer):
    """
    自定义序列化器
    """

    def get_dump_object(self, obj):
        json_data = {}
        json_data.update({'msg_type': MSG_TYPE_MESSAGE})
        json_data.update({'user_id': str(obj.user.id)})
        json_data.update({'msg_id': str(obj.id)})
        json_data.update({'username': str(obj.user.username)})
        json_data.update({'message': str(obj.content)})
        json_data.update({'profile_image': str(obj.user.profile_image.url)})
        json_data.update({'natural_timestamp': calculate_timestamp(obj.timestamp)})
        return json_data
