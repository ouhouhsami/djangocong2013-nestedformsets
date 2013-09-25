# -*- coding: utf8 -*-

from django.views.generic import UpdateView
from nestedformsets import *
from .models import Band
from .forms import BandForm

class BandUpdateView(UpdateView):
    model = Band
    template_name = "music/update.html"

    def get_form_class(self):

        return nested_formset_factory(
            self.model,
            Record,
            Track,
        )  


def flatten(*args):
    for x in args:
        if hasattr(x, '__iter__'):
            for y in flatten(*x):
                yield y
        else:
            yield x


class BandExtendedUpdateView(UpdateView):
    model = Band
    template_name = "music/update.html"

    form_class = BandForm
    
    def form_valid(self, form):
        
        context = self.get_context_data()
        if all(list(flatten([formset.is_valid() for formset in context['formsets']]))):
            for formset in context['formsets']:
                formset.save()
                self.object = form.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super(BandExtendedUpdateView, self).get_context_data(**kwargs)
        context['formsets'] = [f(**self.get_form_kwargs()) for f in extended_nested_formset_factory(self.model)]
        return context