from django.core.serializers.python import Serializer
from django.contrib.humanize.templatetags.humanize import naturaltime


class LazyNotificationEncoder(Serializer):
    """
    Serialize a Notification into JSON.
    There are 3 types
        1. FriendRequest
        2. FriendList
        3. UnreadChatRoomMessage
    """

    def get_dump_object(self, obj):
        json_data = {}
        if obj.get_content_object_type() == "FriendRequest":
            json_data.update({'notification_type': obj.get_content_object_type()})
            json_data.update({'notification_id': str(obj.pk)})
            json_data.update({'verb': obj.verb})
            json_data.update({'is_active': str(obj.content_object.is_active)})
            json_data.update({'is_read': str(obj.read)})
            json_data.update({'natural_timestamp': str(naturaltime(obj.timestamp))})
            json_data.update({'timestamp': str(obj.timestamp)})
            json_data.update({
                # 接收/拒绝 请求，使用js在前端处理
                'actions': {
                    'redirect_url': str(obj.redirect_url),
                },
                "from": {
                    "image_url": str(obj.from_user.profile_image.url)
                }
            })
        if obj.get_content_object_type() == "FriendList":
            json_data.update({'notification_type': obj.get_content_object_type()})
            json_data.update({'notification_id': str(obj.pk)})
            json_data.update({'verb': obj.verb})
            json_data.update({'natural_timestamp': str(naturaltime(obj.timestamp))})
            json_data.update({'is_read': str(obj.read)})
            json_data.update({'timestamp': str(obj.timestamp)})
            json_data.update({
                'actions': {
                    'redirect_url': str(obj.redirect_url),
                },
                "from": {
                    "image_url": str(obj.from_user.profile_image.url)
                }
            })
        return json_data.update({'notification_type': obj.get_content_object_type()})
