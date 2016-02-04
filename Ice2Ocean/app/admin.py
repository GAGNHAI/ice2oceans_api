from django.contrib import admin
from django import forms

class AddToAdmin(admin.ModelAdmin):
    list_display = ('my_url_field',)

    def my_url_field(self, obj):
        return '<a href="%s%s">%s</a>' % ('http://url-to-prepend.com/', obj.url_field, obj.url_field)
    my_url_field.allow_tags = True
    my_url_field.short_description = 'Column description'