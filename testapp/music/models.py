# -*- coding: utf8 -*-
from django.core.urlresolvers import reverse
from django.db import models


class Artist(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class Role(models.Model):
    label = models.CharField(max_length=255)

    def __unicode__(self):
        return self.label


class Band(models.Model):
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(Artist, through='Membership')

    def get_absolute_url(self):
        return reverse('detail', args=[str(self.id)])

    def __unicode__(self):
        return self.name


class Membership(models.Model):
    artist = models.ForeignKey(Artist)
    band = models.ForeignKey(Band)
    roles = models.ManyToManyField(Role)


class Record(models.Model):
    title = models.CharField(max_length=255)
    band = models.ForeignKey(Band)

    #def __unicode__(self):
    #    return self.title


class Track(models.Model):
    title = models.CharField(max_length=255)
    record = models.ForeignKey(Record)
    contributions = models.ManyToManyField(Artist, through="ArtistContribution")

    def __unicode__(self):
        return self.title


class ArtistContribution(models.Model):
    track = models.ForeignKey(Track)
    artist = models.ForeignKey(Artist)
    roles = models.ManyToManyField(Role)
    
    def __unicode__(self):
        try:
            return "%s-%s-%s" % (self.track, self.instrument, self.artist)
        except:
            return None


class Concert(models.Model):
    band = models.ForeignKey(Band)
    date_time = models.DateTimeField()
    place = models.CharField(max_length=255)
    price = models.IntegerField()
    playlist = models.ManyToManyField(Track, through="TrackPlaylist")


class TrackPlaylist(models.Model):
    track = models.ForeignKey(Track)
    concert = models.ForeignKey(Concert)
    order = models.IntegerField()

