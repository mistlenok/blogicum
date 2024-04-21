from django.db.models import Manager
from django.db.models.query import QuerySet
from django.utils.timezone import now


class PostManager(Manager):
    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(
            is_published=True, pub_date__lt=now(), category__is_published=True,
        ).select_related('author', 'location', 'category')
