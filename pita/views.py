from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import Http404
from django.shortcuts import render, redirect
from django.views import View

from anymail.exceptions import AnymailAPIError, AnymailInvalidAddress
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


class ContactView(View):
    template_name = 'contact.html'

    config = settings.CONFIG['contact']
    send_to = config['email']
    prefix = config['prefix']

    def get_message(self, result):
        return self.config['messages'][result].format(email=self.send_to)

    def get(self, request, *args, **kwargs):
        pages = get_pages()
        context = {
            'title': 'Contact',
            'pages': pages,
            'description': self.config['description']
        }

        return render(request, self.template_name, context=context)

    def post(self, request, *args, **kwargs):
        data = request.POST

        name = data.get('name', '')
        from_email = data.get('from_email', '')
        subject = data.get('subject', '')
        message = data.get('message', '')

        # The request contains invalid data
        # This shouldn't happen if the browser enforces the form requirements
        # correctly: the user might have sent a direct POST request
        if not (name and from_email and subject and message):
            messages.error(request, self.get_message('invalid'))
            return self.get(request, *args, **kwargs)

        from_email = '"{}" <{}>'.format(name, from_email)
        subject = '{} {}: {}'.format(self.prefix, name, subject)

        try:
            send_mail(subject, message, from_email, [self.send_to])
        except AnymailAPIError:
            messages.error(request, self.get_message('api_error'))
        except AnymailInvalidAddress:
            messages.error(request, self.get_message('invalid_address'))
        except:
            messages.error(request, self.get_message('error'))
        else:
            messages.success(request, self.get_message('success'))

        return self.get(request, *args, **kwargs)


def page(request, slug):
    pages = get_pages()

    try:
        c = Collection.objects.get(slug=slug)
    except Collection.DoesNotExist:
        pass
    else:
        context = {
            'title': c.title,
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
            'title': t.title,
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
