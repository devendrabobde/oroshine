from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db import transaction
from django.core.cache import cache
import random
import logging

logger = logging.getLogger(__name__)


# =========================================================
# Custom Adapter for Normal Signup
# =========================================================
class CustomAccountAdapter(DefaultAccountAdapter):

    def generate_unique_username(self, txts, max_attempts=100):
        base = slugify(" ".join(str(t) for t in txts if t)) or "user"

        if len(base) > 20:
            base = base[:20]

        username = base
        attempt = 0

        while attempt < max_attempts:
            if not User.objects.filter(username__iexact=username).exists():
                return username
            username = f"{base}{random.randint(1, 9999)}"
            attempt += 1

        import time
        return f"{base}{int(time.time()) % 10000}"

    def populate_username(self, request, user):
        if not user.username:
            if user.email:
                user.username = self.generate_unique_username([user.email.split('@')[0]])
            elif user.first_name or user.last_name:
                user.username = self.generate_unique_username([user.first_name, user.last_name])
            else:
                user.username = self.generate_unique_username(["user"])

    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)

        if user.email:
            user.email = user.email.lower()

        if commit:
            user.save()

        return user

    def clean_username(self, username, shallow=False):
        username = super().clean_username(username, shallow=shallow)
        if len(username) < 3:
            from django.core.exceptions import ValidationError
            raise ValidationError("Username must be at least 3 characters long.")
        return username


# =========================================================
# Custom Adapter for Google / Social Login
# =========================================================
class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def is_open_for_signup(self, request, sociallogin):
        return True

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        if user.email:
            user.email = user.email.lower()

        # Google-specific extra data
        if sociallogin.account.provider == 'google':
            extra = sociallogin.account.extra_data

            if 'picture' in extra:
                request.session['social_avatar_url'] = extra['picture']

            if 'verified_email' in extra:
                user.email_verified = extra.get('verified_email', False)

        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)

        from .models import UserProfile

        with transaction.atomic():
            profile, created = UserProfile.objects.get_or_create(user=user)

            if created and 'social_avatar_url' in request.session:
                avatar_url = request.session.pop('social_avatar_url')

                try:
                    from .tasks import download_social_avatar_task
                    transaction.on_commit(lambda: download_social_avatar_task.delay(user.id, avatar_url))
                except ImportError:
                    logger.warning("Avatar download task not available")

            cache.set(f"user_profile:{user.id}", profile, 1800)

            logger.info(
                f"Social login: User {user.id} ({user.username}) via {sociallogin.account.provider}"
            )

        return user

    # =====================================================
    # Handle login from existing email: auto-link account
    # =====================================================
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

        if not sociallogin.email_addresses:
            return

        email = sociallogin.email_addresses[0].email.lower()

        try:
            existing_user = User.objects.get(email__iexact=email)
            sociallogin.connect(request, existing_user)

            logger.info(f"Linked social account to existing user: {existing_user.username}")

        except User.DoesNotExist:
            pass

        except User.MultipleObjectsReturned:
            existing_user = User.objects.filter(email__iexact=email).first()
            sociallogin.connect(request, existing_user)

    # =====================================================
    # Handle Authentication Errors
    # =====================================================
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        logger.error(f"Social auth error for {provider_id}: {error} - {exception}")

        from django.contrib import messages
        messages.error(
            request,
            f"Authentication with {provider_id.title()} failed. Please try again."
        )
