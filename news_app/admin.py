from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import UserTab, Category, Source, News, PDFDocument, Comment, Analytics, UserPreference

admin.site.register(UserTab)
admin.site.register(Category)
admin.site.register(Source)
admin.site.register(News)
admin.site.register(PDFDocument)
admin.site.register(Comment)
admin.site.register(Analytics)
admin.site.register(UserPreference)
