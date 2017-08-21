from django.http import Http404
from django.shortcuts import render, redirect

from pita.models import Collection, Text, Redirect


def page(request, slug):
    try:
        c = Collection.objects.get(slug=slug)
    except Collection.DoesNotExist:
        pass
    else:
        return render(request, "collection.html", context={'collection': c})

    try:
        t = Text.objects.get(slug=slug)
    except Text.DoesNotExist:
        pass
    else:
        return render(request, "text.html", context={'text': t})

    try:
        r = Redirect.objects.get(slug=slug)
    except Redirect.DoesNotExist:
        raise Http404
    else:
        return redirect(r.link, permanent=False)
