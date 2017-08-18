from django.core.files import File
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify

import os
import PIL.Image
from io import BytesIO


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

    @property
    def filename(self):
        return os.path.basename(self.image.name)


@receiver(pre_save, sender=Artwork)
def update_thumbnail(sender, instance, *args, **kwargs):
    """Updates the thumbnail for an artwork object."""
    artwork = instance

    try:
        previous = Artwork.objects.get(pk=artwork.pk)
    # New object
    except Artwork.DoesNotExist:
        tb = create_thumbnail(artwork)
    else:
        # New file
        if previous.image != artwork.image:
            tb = create_thumbnail(artwork)
        else:
            return

    # Delete the existing thumbnail, if it exists
    if artwork.thumbnail:
        artwork.thumbnail.delete(save=False)

    artwork.thumbnail.save(artwork.filename, File(tb), save=False)


def create_thumbnail(artwork):
    """Creates a 500x500 square thumbnail for an artwork object."""
    artwork.image.open()

    image = PIL.Image.open(artwork.image)

    w = image.width
    h = image.height

    if w > h:
        x1 = 0.5 * w - 0.5 * h
        y1 = 0
        x2 = 0.5 * w + 0.5 * h
        y2 = h
    elif w < h:
        x1 = 0
        y1 = 0.5 * h - 0.5 * w
        x2 = w
        y2 = 0.5 * h + 0.5 * w
    elif w == h:
        x1 = 0
        y1 = 0
        x2 = w
        y2 = h

    bounds = map(int, (x1, y1, x2, y2))

    image = image.crop(bounds)
    image.thumbnail((500, 500), PIL.Image.ANTIALIAS)

    data = BytesIO()
    image.save(data, 'JPEG', quality=85)

    artwork.image.close()
    return data
