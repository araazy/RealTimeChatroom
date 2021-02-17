from datetime import datetime

from django.contrib.humanize.templatetags.humanize import naturalday
from django.core.serializers.python import Serializer

from chat.constants import MSG_TYPE_MESSAGE
from chat.models import PrivateChatroom


def find_or_create_private_chat(user1, user2):
    """
    获取两个用户之间的聊天，如果不存在，创建一个
    """
    try:
        chat = PrivateChatroom.objects.get(user1=user1, user2=user2)
    except PrivateChatroom.DoesNotExist:
        try:
            chat = PrivateChatroom.objects.get(user1=user2, user2=user1)
        except PrivateChatroom.DoesNotExist:
            chat = PrivateChatroom(user1=user1, user2=user2)
            chat.save()
    return chat


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


class LazyChatroomMessageEncoder(Serializer):
    def get_dump_object(self, obj):
        json_data = {}
        json_data.update({'msg_type': MSG_TYPE_MESSAGE})
        json_data.update({'msg_id': str(obj.id)})
        json_data.update({'user_id': str(obj.user.id)})
        json_data.update({'username': str(obj.user.username)})
        json_data.update({'message': str(obj.content)})
        json_data.update({'profile_image': str(obj.user.profile_image.url)})
        json_data.update({'natural_timestamp': calculate_timestamp(obj.timestamp)})
        return json_data
