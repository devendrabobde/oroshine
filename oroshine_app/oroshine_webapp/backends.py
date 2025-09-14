
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailUsernameBackend(BaseBackend):
    """
    Custom authentication backend that allows users to log in using 
    their email address or username.
    
    This backend works alongside Django's ModelBackend and Allauth's backend.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user with email or username
        """
        if username is None or password is None:
            return None
            
        try:
            # Normalize input
            username = username.lower().strip()
            
            # Try to find user by email or username
            user = User.objects.filter(
                Q(email__iexact=username) | Q(username__iexact=username)
            ).first()
            
            if user and user.check_password(password) and user.is_active:
                logger.info(f"Custom backend authentication successful for: {username}")
                return user
            else:
                logger.debug(f"Custom backend authentication failed for: {username}")
                return None
                
        except Exception as e:
            logger.error(f"Error in custom authentication backend: {e}")
            return None
    
    def get_user(self, user_id):
        """
        Get user by ID
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
    
    def user_can_authenticate(self, user):
        """
        Check if user is allowed to authenticate
        """
        is_active = getattr(user, 'is_active', None)
        return is_active or is_active is None