from django.contrib import admin
from django.utils.html import format_html

from pita.models import Artwork, Collection, Page, Redirect, Text


class BaseAdmin(admin.ModelAdmin):
    def get_fields(self, request, obj=None):
        """Hides read-only fields when adding a new object."""
        fields = list(super().get_fields(request, obj=obj))

        out = list()
        for field in fields:
            if field in self.readonly_fields and obj is None:
                continue
            out.append(field)

        return out

    def get_fieldsets(self, request, obj=None):
        fieldsets = list(super().get_fieldsets(request, obj=obj))
        fields = self.get_fields(request, obj=obj)

        out = list()
        for name, options in fieldsets:
            options['fields'] = list(
                filter(lambda f: f in fields, options['fields']))
            out.append((name, options))

        return out


@admin.register(Page)
class PageAdmin(BaseAdmin):
    list_display = ('title', 'slug', 'position')


@admin.register(Collection)
class CollectionAdmin(BaseAdmin):
    list_display = ('title', 'slug', 'items', 'position')
    fields = ('title', 'description', 'position')

    def items(self, collection):
        return collection.artworks.all().count()


@admin.register(Text)
class TextAdmin(BaseAdmin):
    list_display = ('title', 'slug', 'position')
    fields = ('title', 'content', 'position')


@admin.register(Redirect)
class RedirectAdmin(BaseAdmin):
    list_display = ('title', 'slug', 'link', 'position')
    fields = ('title', 'link', 'position')


@admin.register(Artwork)
class ArtworkAdmin(BaseAdmin):
    list_display = (
        'pk', 'title', 'description', 'collection_title',
        'width', 'height',
        'uploaded', 'created', 'position')
    ordering = ('position', '-pk')

    fieldsets = (
        ('Image', {
            'fields': ('image', 'preview', 'dimensions')
        }),
        ('Metadata', {
            'fields': ('title', 'description', 'collection', 'position')
        }),
        ('Dates', {
            'fields': ('uploaded', 'created')
        })
    )
    readonly_fields = ('preview', 'dimensions', 'uploaded')

    def preview(self, artwork):
        """Returns HTML tags to preview this artwork."""
        return format_html('<a href="{0}"><img height="300" src="{0}"></a>',
                           artwork.image.url)

    preview.short_description = 'Preview'

    def dimensions(self, artwork):
        """Returns the dimensions of the image."""
        return "{0} x {1}".format(artwork.width, artwork.height)

    dimensions.short_description = 'Dimensions'

    def collection_title(self, artwork):
        """Returns the title of the artwork's collection."""
        c = artwork.collection
        return '' if c is None else c.title

    collection_title.admin_order_field = 'collection__title'
    collection_title.short_description = 'Collection'
