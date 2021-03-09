from itertools import chain

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.conf import settings

from account.models import Account
from chat.models import PrivateChatroom, ChatroomMessage
from chat.utils import find_or_create_private_chat

DEBUG = False


def private_chat_room_view(request, *args, **kwargs):
    user = request.user
    room_id = request.GET.get("room_id")

    # 没有登陆，重定向
    if not user.is_authenticated:
        return redirect("login")

    context = {}
    if room_id:
        try:
            room = PrivateChatroom.objects.get(pk=room_id)
            context['room'] = room
        except PrivateChatroom.DoesNotExist:
            pass

    # 1. 找到与该用户有关的所有聊天室
    rooms1 = PrivateChatroom.objects.filter(user1=user, is_active=True)
    rooms2 = PrivateChatroom.objects.filter(user2=user, is_active=True)

    # 2. merge the lists
    rooms = list(chain(rooms1, rooms2))
    print(str(len(rooms)))

    """
    m_and_f:
        [
          {
            "message": "hey",
            "friend": "Mitch"
          }, 
          {
            "message": "You there?",
            "friend": "Blake"
          },
        ]
    Where message = The most recent message
    """
    m_and_f = []
    for room in rooms:
        # 找到对方
        if room.user1 == user:
            friend = room.user2
        else:
            friend = room.user1
        m_and_f.append({
            'message': "",
            'friend': friend
        })
    context['m_and_f'] = m_and_f

    context['debug'] = DEBUG
    context['debug_mode'] = settings.DEBUG
    return render(request, "chat/room.html", context)


# Ajax请求，返回或创建一个聊天对话
def create_or_return_private_chat(request, *args, **kwargs):
    user1 = request.user
    payload = {}
    if user1.is_authenticated:
        if request.method == "POST":
            user2_id = request.POST.get("user2_id")
            try:
                user2 = Account.objects.get(pk=user2_id)
                chat = find_or_create_private_chat(user1, user2)
                payload['response'] = "Successfully got the chat."
                payload['chatroom_id'] = chat.id
            except Account.DoesNotExist:
                payload['response'] = "Unable to start a chat with that user."
    else:
        payload['response'] = "You can't start a chat if you are not authenticated."
    return JsonResponse(payload)
