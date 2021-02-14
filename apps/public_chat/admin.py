from django.contrib import admin
from django.core.paginator import Paginator
from django.core.cache import cache

from public_chat.models import PublicChatroom, PublicChatroomMessage


class PublicChatroomAdmin(admin.ModelAdmin):
    list_display = ['id', 'title']
    search_fields = ['id', 'title']
    readonly_fields = ['id', ]

    class Meta:
        model = PublicChatroom


admin.site.register(PublicChatroom, PublicChatroomAdmin)


# Resource: http://masnun.rocks/2017/03/20/django-admin-expensive-count-all-queries/
class CachingPaginator(Paginator):
    def _get_count(self):

        if not hasattr(self, "_count"):
            self._count = None

        if self._count is None:
            try:
                key = "adm:{0}:count".format(hash(self.object_list.query.__str__()))
                self._count = cache.get(key, -1)
                if self._count == -1:
                    self._count = super().count
                    cache.set(key, self._count, 3600)

            except:
                self._count = len(self.object_list)
        return self._count

    count = property(_get_count)


class PublicChatroomMessageAdmin(admin.ModelAdmin):
    list_filter = ['room',  'user', "timestamp"]
    list_display = ['room',  'user', 'content', "timestamp"]
    search_fields = ['room__title', 'user__username', 'content']
    readonly_fields = ['id', "user", "room", "timestamp"]

    show_full_result_count = False
    paginator = CachingPaginator

    class Meta:
        model = PublicChatroomMessage


admin.site.register(PublicChatroomMessage, PublicChatroomMessageAdmin)
