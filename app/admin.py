from django.contrib import admin

from app.models import Comments,Post, Tag, Profile, WebSiteMeta, Expense, Category, Transaction

# Register your models here.
admin.site.register(Post)
admin.site.register(Tag)
admin.site.register(Comments)
admin.site.register(Profile)
admin.site.register(WebSiteMeta)
admin.site.register(Expense)
admin.site.register(Category)
admin.site.register(Transaction)

