from django.contrib import admin
from django.utils.text import Truncator

from .models import Category, Location, Post

MAX_PER_PAGE = 20


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'short_text',
        'pub_date',
        'author',
        'location',
        'category',
        'is_published',
        'created_at'
    )
    list_editable = (
        'is_published',
    )
    search_fields = (
        'title',
        'text',
        'author__username',
        'location__name',
        'category__title'
    )
    list_filter = (
        'author',
        'location',
        'category',
        'is_published',
        'pub_date'
    )
    ordering = ['-pub_date']
    list_per_page = MAX_PER_PAGE
    date_hierarchy = 'pub_date'
    list_display_links = ('title',)

    def short_text(self, obj):
        return Truncator(obj.text).chars(30, truncate='...')
    short_text.short_description = 'Текст'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'slug',
        'created_at',
        'is_published'
    )
    search_fields = (
        'title',
        'slug',
        'description'
    )
    list_filter = (
        'is_published',
        'created_at'
    )
    ordering = ['title']
    list_per_page = MAX_PER_PAGE


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'is_published',
        'created_at'
    )
    search_fields = ('name',)
    list_filter = (
        'is_published',
        'created_at'
    )
    ordering = ['name']
    list_per_page = MAX_PER_PAGE


admin.site.empty_value_display = 'Не задано'
