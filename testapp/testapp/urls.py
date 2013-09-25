from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.detail import DetailView

from music.models import Band
from music.views import BandUpdateView, BandExtendedUpdateView

admin.autodiscover()

urlpatterns = patterns('',
	url(r'^read/(?P<pk>[\d]+)/$', DetailView.as_view(model=Band), name="detail"),
    url(r'^update/(?P<pk>[\d]+)/$', BandUpdateView.as_view(), name='update'),
    url(r'^extended-update/(?P<pk>[\d]+)/$', BandExtendedUpdateView.as_view(), name="extended-update"),
    url(r'^admin/', include(admin.site.urls)),
)
