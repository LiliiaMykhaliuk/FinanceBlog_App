"""
This module registers various models with the Django admin site 
to enable easy management through the Django admin interface.
"""


from django.contrib import admin
from app.models import Comments,Post, Tag, Profile, WebSiteMeta, Category, Transaction

# Register models with the Django admin site
admin.site.register(Post)
admin.site.register(Tag)
admin.site.register(Comments)
admin.site.register(Profile)
admin.site.register(WebSiteMeta)
admin.site.register(Category)
admin.site.register(Transaction)
