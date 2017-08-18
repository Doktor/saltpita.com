import os
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


def get_artwork_path(artwork, original_name):
    root, ext = os.path.splitext(original_name)
    return "{pk:04}.{ext}".format(pk=artwork.pk, ext=ext.lstrip('.'))


def get_thumbnail_path(artwork, original_name):
    return "thumb/{full}".format(full=get_artwork_path(artwork, original_name))


class Artwork(models.Model):
    image = models.ImageField(
        upload_to=get_artwork_path,
        width_field='width', height_field='height')
    thumbnail = models.ImageField(
        upload_to=get_thumbnail_path, editable=False)

    width = models.PositiveIntegerField(default=0, editable=False)
    height = models.PositiveIntegerField(default=0, editable=False)

    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    collection = models.ForeignKey(Collection, on_delete=models.SET_NULL,
        related_name='artworks', blank=True, null=True)

    uploaded = models.DateField(auto_now_add=True)
    created = models.DateField(blank=True, null=True)

    position = models.PositiveIntegerField(default=0)
