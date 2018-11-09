from django.contrib import messages
from django.core.mail import send_mail
from django.http import Http404
from django.shortcuts import render, redirect
from django.views import View

from anymail.exceptions import AnymailAPIError, AnymailInvalidAddress
from constance import config
from pita.models import Artwork, Collection, Page, Redirect, Text


def get_pages():
    return Page.objects.select_subclasses().order_by('position')


def index(request):
    pages = get_pages()
    artworks = Artwork.objects.filter(collection=None)

    context = {
        'artworks': artworks,
        'pages': pages,
    }
    return render(request, 'index.html', context=context)


class ContactView(View):
    template_name = 'contact.html'

    send_to = f"{config.EMAIL_NAME} <{config.EMAIL_ADDRESS}>"

    @staticmethod
    def get_message(status):
        return getattr(config, status).format(email=config.EMAIL_ADDRESS)

    def get(self, request, *args, **kwargs):
        pages = get_pages()
        context = {
            'title': config.CONTACT_TITLE,
            'pages': pages,
            'form': kwargs.pop('form', None),
        }

        return render(request, self.template_name, context=context)

    def post(self, request, *args, **kwargs):
        data = request.POST

        name = data.get('name', '')
        sent_by = data.get('from_email', '')
        subject = data.get('subject', '')
        message = data.get('message', '')

        form = {
            'name': name,
            'sent_by': sent_by,
            'subject': subject,
            'message': message,
        }

        # The request contains invalid data
        # This shouldn't happen if the browser enforces the form requirements
        # correctly: the user might have sent a direct POST request
        if not (name and sent_by and subject and message):
            messages.error(request, self.get_message('INVALID'))
            return self.get(request, *args, **kwargs)

        sent_by = '"{}" <{}>'.format(name, sent_by)
        subject_line = '{} {}: {}'.format(config.SUBJECT_PREFIX, name, subject)

        try:
            send_mail(subject_line, message, sent_by, [self.send_to])
        except AnymailAPIError as e:
            messages.error(request, self.get_message('API_ERROR'))
        except AnymailInvalidAddress:
            messages.error(request, self.get_message('INVALID_ADDRESS'))
        except:
            messages.error(request, self.get_message('ERROR'))
        else:
            form = None
            messages.success(request, self.get_message('SUCCESS'))

        return self.get(request, *args, form=form, **kwargs)


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
