from celery import group
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin

from misirlou.models import Manifest
from misirlou.helpers.manifest_utils.errors import ErrorMap
from misirlou.tasks import test_manifest, import_single_manifest
ERROR_MAP = ErrorMap()


def reimport(modeladmin, request, queryset):
    g = group([import_single_manifest.s(None, man.remote_url, force=True) for man in queryset]).skew(start=1, step=1)
    g.apply_async()
reimport.short_description = "Re-import manifests"


def retest(modeladmin, request, queryset):
    g = group([test_manifest.s(str(man.id)) for man in queryset]).skew(start=1, step=1)
    g.apply_async()
retest.short_description = "Run tests on manifests"


class ErrorFilter(admin.SimpleListFilter):
    title = _('errors',)
    parameter_name = 'error'

    def lookups(self, request, model_admin):
        lst = []
        for k,n,v in ERROR_MAP.values():
            num = Manifest.objects.with_error(k).count()
            if num > 0:
                lst.append((k, _(n + " ({})".format(num))))
        return lst

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return Manifest.objects.with_error(int(self.value()))


class WarningFilter(admin.SimpleListFilter):
    title = _('warnings')
    parameter_name = 'warnings'

    def lookups(self, request, model_admin):
        lst = []
        for k,n,v in ERROR_MAP.values():
            num = Manifest.objects.with_warning(k).count()
            if num > 0:
                lst.append((k, _(n + " ({})".format(num))))
        return lst

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return Manifest.objects.with_warning(int(self.value()))


@admin.register(Manifest)
class ManifestAdmin(admin.ModelAdmin):
    list_display = ('remote_url', 'created')
    exclude = ('_error', '_warnings')
    readonly_fields = ('id', 'remote_url', 'manifest_hash',
                       'warnings', 'error', 'is_valid', 'last_tested')
    search_fields = ['remote_url']
    list_filter = ['is_valid', ErrorFilter, WarningFilter]
    actions = [reimport, retest]

    def has_add_permission(self, request):
        return False
