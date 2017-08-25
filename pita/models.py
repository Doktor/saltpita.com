from django.core.files import File
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.text import slugify

import os
import PIL.Image
import uuid
from io import BytesIO


class Page(models.Model):
    title = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=20, blank=True, unique=True)
    position = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return "Page: {}".format(self.title)

    class Meta:
        abstract = True
        ordering = ['position', 'pk']


class Collection(Page):
    description = models.TextField(blank=True)


class Text(Page):
    content = models.TextField(blank=True)


class Redirect(Page):
    link = models.URLField(max_length=500)


def get_artwork_path(artwork, original_name):
    _, ext = os.path.splitext(original_name)
    ext = ext.lstrip('.')

    if artwork.pk is not None:
        return "{base:04d}.{ext}".format(base=artwork.pk, ext=ext)
    else:
        return "{base}.{ext}".format(base=uuid.uuid4(), ext=ext)


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

    def __str__(self):
        return "Artwork #{}".format(self.pk)

    class Meta:
        ordering = ['position', 'pk']


@receiver(pre_save, sender=Artwork, dispatch_uid='pita.models.update_thumb')
def update_thumbnail(sender, instance, *args, **kwargs):
    """Updates the thumbnail for an artwork object."""
    artwork = instance

    if hasattr(artwork, '_rename'):
        del artwork._rename
        return

    # New object
    if artwork.pk is None:
        tb = create_thumbnail(artwork)
    else:
        # Existing object, check if the image changed
        current = Artwork.objects.get(pk=artwork.pk)
        if current.image == artwork.image:
            return

        artwork._update = True
        tb = create_thumbnail(artwork)

    # Delete the existing thumbnail, if it exists
    if artwork.thumbnail:
        artwork.thumbnail.delete(save=False)

    artwork.thumbnail.save(artwork.filename, File(tb), save=False)


@receiver(post_save, sender=Artwork, dispatch_uid='pita.models.rename_files')
def rename_files(sender, instance, created, *args, **kwargs):
    """Renames image files after an artwork object is created or updated."""
    artwork = instance

    # Existing object, new image
    if hasattr(artwork, '_update'):
        assert not created
        del artwork._update

        # We only have to rename the image: the old thumbnail is deleted in
        # the pre-save receiver, which frees up the filename for the new thumb
        image = artwork.image
        current_path = image.path
        image.name = get_artwork_path(artwork, image.name)

        os.remove(image.path)
        os.rename(current_path, image.path)

        artwork._rename = True
        artwork.save()
        return

    if not created:
        return

    # Rename the image file
    image = artwork.image
    old_path = image.path
    image.name = get_artwork_path(artwork, image.name)
    os.rename(old_path, image.path)

    # Rename the thumbnail file
    thumbnail = artwork.thumbnail
    old_path = thumbnail.path
    thumbnail.name = get_thumbnail_path(artwork, thumbnail.name)
    os.rename(old_path, thumbnail.path)

    artwork._rename = True
    artwork.save()


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

    return data
