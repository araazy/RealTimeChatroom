from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class MyAccountManager(BaseUserManager):
    """
    自定义用户管理器

    自定义create a new user
    自定义create a superuser
    """
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("Users must have an email address.")
        if not username:
            raise ValueError("Users must have a username.")
        user = self.model(
            # 通过降低电子邮件地址的域部分来规范化电子邮件地址
            email=self.normalize_email(email),
            username=username,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


# 头像存放地址
def get_profile_image_filepath(self, filename):
    return f'profile_images/{str(self.pk)}/{"profile_image.png"}'


# 默认图片
def get_default_profile_image():
    return "profile/profile_image.png"


class Account(AbstractBaseUser):
    """
    使用AbstracBaseUser自定义用户模型
    """
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    username = models.CharField(max_length=30, unique=True)
    date_joined = models.DateTimeField(verbose_name="date joined", auto_now_add=True)
    last_login = models.DateTimeField(verbose_name="last login", auto_now=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    profile_image = models.ImageField(max_length=255, upload_to=get_profile_image_filepath, null=True, blank=True,
                                      default=get_default_profile_image)
    hide_email = models.BooleanField(default=True)

    objects = MyAccountManager()

    # 把USERNAME_FIELD设为email，USERNAME_FIELD是描述模型字段名的唯一标识符，这里我设置为邮箱
    USERNAME_FIELD = 'email'
    # 必填字段
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username

    # 截取文件名
    def get_profile_image_filename(self):
        return str(self.profile_image)[str(self.profile_image).index(f'profile_images/{str(self.pk)}/'):]

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True




