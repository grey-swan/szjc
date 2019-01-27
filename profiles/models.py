from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=16, default='游客', blank=True)
    phone = models.CharField(max_length=16, default='', blank=True)
    picture_file = models.CharField(max_length=64, default='default.png')

    '''
    def __str__(self):
        return {'nickname': self.nickname}

    def __unicode__(self):
        return {'nickname': self.nickname}
    '''


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = UserProfile()
        profile.user = instance
        profile.save()


# post_save.connect(create_user_profile, sender=User)
