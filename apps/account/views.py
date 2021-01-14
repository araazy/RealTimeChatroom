import os

import cv2
from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.core import files
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from account.forms import RegistrationForm, AccountAuthenticationForm, AccountUpdateForm
from account.models import Account
from friend.friend_request_status import FriendRequestStatus
from friend.models import FriendList, FriendRequest
from friend.utils import get_friend_request_or_false
from .utils import (
    get_redirect_if_exists,
    save_temp_profile_image_from_base64String
)


# 用户注册视图
def register_view(request, *args, **kwargs):
    user = request.user
    if user.is_authenticated:
        return HttpResponse(f"You are already authenticated as {user.email}")

    context = {}
    if request.POST:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # form可以通过表单数据创建对象，并保存到数据库
            form.save()
            email = form.cleaned_data.get('email').lower()
            raw_password = form.cleaned_data.get('password1')
            account = authenticate(email=email, password=raw_password)
            # login
            login(request, account)
            # 回到来访问的页面
            destination = get_redirect_if_exists(request)

            return redirect(destination)
        else:
            context['registration_form'] = form

    return render(request, 'account/register.html', context)


# 退出登录视图
def logout_view(request, *args, **kwargs):
    logout(request)
    return redirect("home")


# 登录视图
def login_view(request, *args, **kwargs):
    context = {}
    user = request.user
    if user.is_authenticated:
        return redirect("home")

    if request.POST:
        form = AccountAuthenticationForm(request.POST)
        if form.is_valid():
            email = request.POST['email']
            password = request.POST['password']
            user = authenticate(email=email, password=password)
            if user:
                # 认证成功，登录
                login(request, user)
                destination = get_redirect_if_exists(request)
                return redirect(destination)
        else:
            context['login_form'] = form
    return render(request, "account/login.html", context)


# 用户个人信息视图
def account_view(request, *args, **kwargs):
    """
    Friend Requests 提示框逻辑：
        √ is_self  # 只有自己能看到
          × is_friend   #
                -1: NO_REQUEST_SENT
                0: THEM_SENT_TO_YOU
                1: YOU_SENT_TO_THEM

    """
    context = {}
    # 获取当前访问的用户profile的user_id
    user_id = kwargs.get('user_id')
    try:
        account = Account.objects.get(pk=user_id)
    except Account.DoesNotExist:
        return HttpResponse("That user doesn't exist.")
    if account:
        context['id'] = account.id
        context['username'] = account.username
        context['email'] = account.email
        context['profile_image'] = account.profile_image.url
        context['hide_email'] = account.hide_email

        try:
            friend_list = FriendList.objects.get(user=account)
        except FriendList.DoesNotExist:
            friend_list = FriendList(user=account)
            friend_list.save()
        friends = friend_list.friends.all()
        context['friends'] = friends

        # 模板参数
        is_self = True
        is_friend = False
        # 获取当前用户
        user = request.user
        request_sent = FriendRequestStatus.NO_REQUEST_SENT.value
        friend_requests = None
        if user.is_authenticated and user != account:
            is_self = False
            # 如果被访问用户的friend_list中有当前用户user.id，说明是朋友
            if friends.filter(pk=user.id):
                is_friend = True
            else:
                is_friend = False
                # CASE1: 当前被查看用户 对 当前登录用户发送了好友请求
                if get_friend_request_or_false(sender=account, receiver=user):
                    request_sent = FriendRequestStatus.THEM_SENT_TO_YOU.value
                    context['pending_friend_request_id'] = get_friend_request_or_false(sender=account, receiver=user).id
                # CASE2: 当前登录用户 对 当前被查看用户发送了好友请求
                elif get_friend_request_or_false(sender=user, receiver=account):
                    request_sent = FriendRequestStatus.YOU_SENT_TO_THEM.value
                # CASE3: 没有发送 / 接收好友请求
                else:
                    request_sent = FriendRequestStatus.NO_REQUEST_SENT.value
        elif not user.is_authenticated:
            is_self = False
        # You are looking at your own profile
        else:
            try:
                friend_requests = FriendRequest.objects.filter(receiver=user, is_active=True)
            except FriendRequest.DoesNotExist:
                # 没有好友请求，pass
                pass

        # 传递模板参数
        context['is_self'] = is_self
        context['is_friend'] = is_friend
        context['BASE_URL'] = settings.BASE_URL
        context['request_sent'] = request_sent
        context['friend_requests'] = friend_requests
        return render(request, "account/account.html", context)


# 编辑个人信息视图
def edit_account_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        return redirect("login")
    user_id = kwargs.get("user_id")
    try:
        account = Account.objects.get(pk=user_id)
    except Account.DoesNotExist:
        return HttpResponse("Something went wrong.")
    if account.pk != request.user.pk:
        return HttpResponse("You cannot edit someone else's profile.")
    context = {}
    if request.POST:
        form = AccountUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():  # 更新成功，保存并返回
            form.save()
            return redirect("account:view", user_id=account.pk)
        else:
            # set initial values
            form = AccountUpdateForm(request.POST, instance=request.user,
                                     initial={
                                         "id": account.pk,
                                         "email": account.email,
                                         "username": account.username,
                                         "profile_image": account.profile_image,
                                         "hide_email": account.hide_email,
                                     }
                                     )
            context['form'] = form
    else:
        # 编辑页面需要设置初始值
        form = AccountUpdateForm(
            initial={
                "id": account.pk,
                "email": account.email,
                "username": account.username,
                "profile_image": account.profile_image,
                "hide_email": account.hide_email,
            }
        )
        context['form'] = form
    context['DATA_UPLOAD_MAX_MEMORY_SIZE'] = settings.DATA_UPLOAD_MAX_MEMORY_SIZE
    return render(request, "account/edit_account.html", context)


# 裁剪图片视图
def crop_image_view(request, *args, **kwargs):
    payload = {}
    user = request.user
    if request.POST and user.is_authenticated:
        try:
            imageString = request.POST.get("image")
            print(imageString[:100])
            url = save_temp_profile_image_from_base64String(imageString, user)
            img = cv2.imread(url)
            print("crop url: ", url)
            cropX = int(float(str(request.POST.get("cropX"))))
            cropY = int(float(str(request.POST.get("cropY"))))
            cropWidth = int(float(str(request.POST.get("cropWidth"))))
            cropHeight = int(float(str(request.POST.get("cropHeight"))))

            if cropX < 0:
                cropX = 0
            if cropY < 0:
                cropY = 0
            # crop
            crop_img = img[cropY:cropY + cropHeight, cropX:cropX + cropWidth]
            cv2.imwrite(url, crop_img)
            user.profile_image.delete()
            user.profile_image.save("profile_image.png", files.File(open(url, "rb")))
            user.save()
            payload['result'] = "success"
            payload['cropped_profile_image'] = user.profile_image.url
            os.remove(url)
        except Exception as e:
            print("exception: " + str(e))
            payload['result'] = "error"
            payload['exception'] = str(e)

    return JsonResponse(payload)


# 搜索用户视图
def account_search_view(request, *args, **kwargs):
    context = {}
    if request.method == "GET":
        search_query = request.GET.get("q")
        if len(search_query) > 0:

            # get: single, filter: multiple
            search_results = Account.objects.filter(
                Q(username__icontains=search_query) | Q(email__icontains=search_query)
            )
            user = request.user
            accounts = []  # account, is_friend, [(account1, True), (...), ...]
            if user.is_authenticated:
                # get the authenticated users friend list
                try:
                    auth_user_friend_list = FriendList.objects.get(user=user)
                except FriendList.DoesNotExist:
                    # 如果用户暂时没有FriendList，创建一个
                    friend_list = FriendList(user=user)
                    friend_list.save()
                    auth_user_friend_list = FriendList.objects.get(user=user)
                # 当前登录用户，和搜索结果中的用户是否为朋友
                for account in search_results:
                    accounts.append((account, auth_user_friend_list.is_mutual_friend(account)))
                context['accounts'] = accounts
            else:
                for account in search_results:
                    accounts.append((account, False))
                context['accounts'] = accounts

    return render(request, "account/search_results.html", context)
