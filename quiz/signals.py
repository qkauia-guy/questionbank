from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver


@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    from .models import UserProfile  # 延遲匯入以避免循環引用錯誤

    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, "userprofile"):
            instance.userprofile.save()
