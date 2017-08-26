from django.http import Http404
from django.shortcuts import render, redirect

from itertools import chain

from pita.models import Collection, Text, Redirect


def page(request, slug):
    # TODO: https://stackoverflow.com/questions/18742870/
    pages = sorted(chain(
        Collection.objects.all(), Text.objects.all(), Redirect.objects.all()),
        key=lambda item: item.title.lower()
    )

    try:
        c = Collection.objects.get(slug=slug)
    except Collection.DoesNotExist:
        pass
    else:
        context = {
            'collection': c,
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
