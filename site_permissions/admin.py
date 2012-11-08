from django.contrib import admin
from django.contrib import auth
from django.forms import ModelMultipleChoiceField
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from guardian.admin import GuardedModelAdmin
from guardian.shortcuts import get_objects_for_user, assign, remove_perm

class SiteAdmin(GuardedModelAdmin):
    pass

admin.site.unregister(Site)
admin.site.register(Site, SiteAdmin)

class UserForm(auth.forms.UserChangeForm):
    sites = ModelMultipleChoiceField(Site.objects.all(), required=False)
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        # DJANGO YOU SUCK
        if 'instance' in kwargs and hasattr(kwargs['instance'], 'sites'):
            self.fields['sites'].initial = [s.id for s in kwargs['instance'].sites]



class UserAdmin(auth.admin.UserAdmin):
    form = UserForm
    fieldsets = auth.admin.UserAdmin.fieldsets + (
        ('This user can edit the following sites', {
            'fields': ('sites',)
            }
         ),
        )

    def save_form(self, request, form, change):
        obj = super(type(self), self).save_form(request, form, change)
        try:
            obj.sites = form.cleaned_data['sites']
        except KeyError:
            obj.sites = []
        return obj

    def save_model(self, request, obj, model, change):
        if hasattr(obj, 'sites'):
            existing = get_objects_for_user(obj, 'change_site_content', Site)
            for s in obj.sites:
                if not s in existing:
                    assign('change_site_content', obj, s)
            for s in existing:
                if not s in obj.sites:
                    remove_perm('change_site_content', obj, s)

        return super(type(self), self).save_model(request, obj, model, change)

    def get_object(self, request, object_id):
        obj = super(type(self), self).get_object(request, object_id)
        if not obj is None and not hasattr(obj, "sites"):
            obj.sites = get_objects_for_user(obj, 'change_site_content', Site)
        return obj
    pass

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
