from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from rest_framework.authtoken.models import Token

from .models import Sample, Sheet, SheetItem


# 创建样品后自动生成流转单记录
@receiver(post_save, sender=Sample, dispatch_uid="sample_post_save")
def create_sheet(sender, instance=None, created=False, **kwargs):
    if created:
        Sheet.objects.create(sample=instance)


# @receiver(post_save, sender=SheetItem, dispatch_uid="sheet_post_save")
# def create_sheet(sender, instance=None, created=False, **kwargs):
#     if created:
#         if instance.sheet.perform:
#             Sheet.objects.create(sample=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
