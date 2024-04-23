from django.contrib import admin
from django.contrib.auth.models import Group
from django.db.models import Count

from .models import Category, Comment, Location, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'author',
        'text',
        'category',
        'pub_date',
        'location',
        'is_published',
        'created_at',
        'comments_count',
    )
    list_display_links = ('title',)
    list_editable = (
        'category',
        'is_published',
        'location',
    )
    list_filter = ('created_at',)
    empty_value_display = 'Не задано'

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            comment_count=Count('comments'))

    @admin.display(description='Количество комментариев')
    def comments_count(self, request):
        return request.comment_count


class PostInline(admin.StackedInline):
    model = Post
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = (PostInline,)
    list_display = ('title',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('text', 'post', 'created_at',)


admin.site.register(Location)
admin.site.unregister(Group)
