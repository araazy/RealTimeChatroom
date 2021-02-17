from datetime import datetime

from django.contrib.humanize.templatetags.humanize import naturalday

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
