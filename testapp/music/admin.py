from django.contrib import admin

from .models import *


class BandAdmin(admin.ModelAdmin):
    pass


admin.site.register(Band, BandAdmin)
admin.site.register(Artist)
admin.site.register(Role)
admin.site.register(Record)
admin.site.register(Track)
admin.site.register(Concert)