from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from allauth.account.signals import user_signed_up
from django.core.cache import cache
from django.db import transaction
import logging
from .metrics import active_users, pending_appointments


from .models import UserProfile

logger = logging.getLogger(__name__)



@receiver(post_save, sender=User)
def track_active_users(sender, instance, created, **kwargs):
    count = User.objects.filter(is_active=True).count()
    active_users.set(count)





@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create profile only on user creation"""
    if created and not kwargs.get('raw', False):
        # Use get_or_create to prevent race conditions
        try:
            profile, profile_created = UserProfile.objects.get_or_create(
                user=instance,
                defaults={}
            )
            if profile_created:
                logger.info(f"Profile created for user {instance.id}")
                cache.set(f'user_profile:{instance.id}', profile, 1800)
        except Exception as e:
            logger.error(f"Error creating profile: {e}")


@receiver(user_signed_up)
def handle_user_signed_up(request, user, **kwargs):
    """Handle allauth signup"""
    try:
        # Ensure profile exists (might already be created by post_save)
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        sociallogin = kwargs.get('sociallogin', None)
        if sociallogin:
            logger.info(f"Social signup: {user.username} via {sociallogin.account.provider}")
            
            if sociallogin.account.provider == 'google':
                extra_data = sociallogin.account.extra_data
                if 'picture' in extra_data:
                    request.session['social_avatar_url'] = extra_data.get('picture')
        
        cache.set(f'user_profile:{user.id}', profile, 1800)
        
        # Clear rate limits
        if hasattr(request, 'META'):
            identifier = request.META.get('REMOTE_ADDR', 'unknown')
            cache.delete(f"register:{identifier}")
            cache.delete(f"login:{identifier}")
    
    except Exception as e:
        logger.error(f"Error in user_signed_up: {e}", exc_info=True)