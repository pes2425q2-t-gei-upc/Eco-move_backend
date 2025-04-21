import os
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

def create_social_apps():
    site = Site.objects.get_or_create(id=1, defaults={'domain': 'localhost', 'name': 'Localhost'})[0]

    social_apps = [
        {
            'provider': 'google',
            'name': 'Google Login',
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'secret': os.getenv('GOOGLE_SECRET'),
        },
        {
            'provider': 'github',
            'name': 'GitHub Login',
            'client_id': os.getenv('GITHUB_CLIENT_ID'),
            'secret': os.getenv('GITHUB_SECRET'),
        }
    ]

    for app in social_apps:
        if not SocialApp.objects.filter(provider=app['provider']).exists():
            sa = SocialApp.objects.create(
                provider=app['provider'],
                name=app['name'],
                client_id=app['client_id'],
                secret=app['secret'],
            )
            sa.sites.add(site)
