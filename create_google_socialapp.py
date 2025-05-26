# create_google_socialapp.py

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecomove_backend.settings") 
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

def run():
    site = Site.objects.get(id=1)
    site.domain = "tusitio.com"  # Reemplaza con tu dominio real
    site.save()

    app, created = SocialApp.objects.get_or_create(
        provider='google',
        name='Google OAuth',
        defaults={
            'client_id': 'GOOGLE_CLIENT_ID',
            'secret': '',
        }
    )
    if created:
        print("✅ SocialApp creado.")
    else:
        print("ℹ️ SocialApp ya existía.")

    app.sites.add(site)
    print(f"✅ Asociado al sitio: {site.domain}")

if __name__ == '__main__':
    run()
