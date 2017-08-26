from django.http import Http404
from django.shortcuts import render, redirect

from itertools import chain

from pita.models import Artwork, Collection, Text, Redirect


def get_pages():
    # TODO: https://stackoverflow.com/questions/18742870/
    return sorted(chain(
        Collection.objects.all(), Text.objects.all(), Redirect.objects.all()),
        key=lambda item: item.title.lower()
    )


def index(request):
    pages = get_pages()
    artworks = Artwork.objects.all()

    context = {
        'artworks': artworks,
        'pages': pages,
    }
    return render(request, 'index.html', context=context)


def page(request, slug):
    pages = get_pages()

    try:
        c = Collection.objects.get(slug=slug)
    except Collection.DoesNotExist:
        pass
    else:
        context = {
            'collection': c,
            'artworks': c.artworks,
            'pages': pages,
        }
        return render(request, "collection.html", context=context)

    try:
        t = Text.objects.get(slug=slug)
    except Text.DoesNotExist:
        pass
    else:
        context = {
            'text': t,
            'pages': pages,
        }
        return render(request, "text.html", context=context)

    try:
        r = Redirect.objects.get(slug=slug)
    except Redirect.DoesNotExist:
        raise Http404
    else:
        return redirect(r.link, permanent=False)
