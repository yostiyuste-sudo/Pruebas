import hashlib
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def gravatar_url(email, size=40):
    """
    Returns the Gravatar URL for the given email.
    If no avatar is found, it returns HTTP 404 (d=404) so that the 'onerror'
    attribute on the img tag can trigger and hide the broken image.
    """
    if not email:
        email = ''
    email_encoded = email.strip().lower().encode('utf-8')
    email_hash = hashlib.md5(email_encoded).hexdigest()
    # d=404 returns a 404 error if there is no image associated with this email
    url = f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=404"
    return mark_safe(url)
