from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import slugify

import os
import PIL.Image
import uuid
from io import BytesIO
from markdown import markdown
from model_utils.managers import InheritanceManager


class Page(models.Model):
    objects = InheritanceManager()

    title = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=20, blank=True, unique=True)
    position = models.PositiveIntegerField(default=0)

    reserved_titles = ['admin', 'contact']

    def clean(self):
        if self.title.lower() in self.reserved_titles:
            raise ValidationError("The page title '{}' is reserved for "
                "internal use.".format(self.title))

    def get_absolute_url(self):
        return reverse('page', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return "Page: {}".format(self.title)

    class Meta:
        ordering = ['position', '-pk']


class Collection(Page):
    description = models.TextField(blank=True)


class Text(Page):
    content = models.TextField(
        blank=True, help_text="Markdown formatting supported")
    html = models.TextField(blank=True, editable=False)


@receiver(pre_save, sender=Text, dispatch_uid='pita.models.parse_markdown')
def parse_markdown(sender, instance, *args, **kwargs):
    """Parses the content of a text page and updates the stored HTML."""
    instance.html = markdown(instance.content)


class Redirect(Page):
    link = models.URLField(max_length=500)


def get_artwork_path(artwork, original_name, ext=None):
    if ext is None:
        _, ext = os.path.splitext(original_name)
        ext = ext.lstrip('.')

    if artwork.pk is not None:
        return "{base:04d}.{ext}".format(base=artwork.pk, ext=ext)
    else:
        return "{base}.{ext}".format(base=uuid.uuid4(), ext=ext)


def get_thumbnail_path(artwork, original_name):
    return "thumb/{full}".format(
        full=get_artwork_path(artwork, original_name, ext='jpg'))


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

    @property
    def summary(self):
        """The summary for this item, used for link/image alt text."""
        return self.description or self.title or str(self)

    def __str__(self):
        return "Artwork #{}".format(self.pk)

    class Meta:
        ordering = ['position', '-pk']


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


def create_thumbnail(artwork, size=(400, 400)):
    """Creates a square thumbnail for an artwork object."""
    artwork.image.open()

    image = PIL.Image.open(artwork.image)

    if image.format != 'JPEG':
        image = image.convert('RGB')

    # Upscale small images
    if image.size < size:
        w, h = image.size
        ratio = max(size[0] / w, size[1] / h)
        image = image.resize((w * ratio, h * ratio), PIL.Image.BICUBIC)

    w, h = image.size

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
    image.thumbnail(size)

    data = BytesIO()
    image.save(data, 'JPEG', quality=75, optimize=True)

    return data


def update_positions(sender, instance, *args, **kwargs):
    item = instance

    if hasattr(item, '_reposition'):
        del item._reposition
        return

    # Existing object: check if the position changed
    if item.pk is not None:
        current = sender.objects.get(pk=item.pk)
        if current.position == item.position:
            return

    new = item.position

    # Select other items in the new position
    query = Q(position=new) & ~Q(pk=item.pk)

    if not sender.objects.filter(query):
        return

    # Select other items in positions >= the new position
    query = Q(position__gte=new) & ~Q(pk=item.pk)

    pages = sender.objects.filter(query)

    for item in pages:
        item.position += 1
        item._reposition = True

    for item in pages:
        item.save()

pre_save.connect(update_positions, sender=Page,
                 dispatch_uid='pita.models.update_page_positions')
pre_save.connect(update_positions, sender=Artwork,
                 dispatch_uid='pita.models.update_artwork_positions')
