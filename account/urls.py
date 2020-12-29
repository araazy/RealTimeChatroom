from django.urls import path
from account.views import (
    account_view,
    edit_account_view,
    crop_image_view,
)
app_name = "account"

urlpatterns = [
    path('<user_id>/', account_view, name="view"),
    path('<user_id>/edit/', edit_account_view, name="edit"),
    path('<user_id>/edit/cropImage', crop_image_view, name="crop_image"),
]
