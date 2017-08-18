from django.db import models
from django.utils.text import slugify


class Page(models.Model):
    title = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=20, blank=True, unique=True)
    position = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class Collection(Page):
    description = models.TextField(blank=True)


class Text(Page):
    content = models.TextField(blank=True)


class Redirect(Page):
    link = models.URLField(max_length=500)
