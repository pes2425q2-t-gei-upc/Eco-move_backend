from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.contrib.auth import get_user_model
from django.http import JsonResponse

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Si el usuario ya está logueado, no hacemos nada
        if request.user.is_authenticated:
            return

        email = sociallogin.account.extra_data.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass  # Si no existe, que siga el flujo normal
        else:
            raise ImmediateHttpResponse(JsonResponse({'error': 'No email in social login data'}, status=400))
