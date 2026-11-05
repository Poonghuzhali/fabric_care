from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """Allow staff sign-in with email or username."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if not username or password is None:
            return None
        login = username.strip()
        user = (
            User.objects.filter(email__iexact=login).first()
            or User.objects.filter(username__iexact=login).first()
        )
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
