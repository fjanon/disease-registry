from django.conf import settings
from django.conf.urls.defaults import patterns
from django.contrib import admin
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404
import django.forms
import json

from admin_forms import *
from models import *
from registry.patients.models import Patient


class GeneAdmin(admin.ModelAdmin):
    list_display = ["symbol", "name", "status", "chromosome"]
    search_fields = ["symbol", "name"]

    def get_urls(self):
        urls = super(GeneAdmin, self).get_urls()
        local_urls = patterns("",
            (r"search/(.*)$", self.admin_site.admin_view(self.search))
        )
        return local_urls + urls

    def search(self, request, term):
        genes = Gene.objects.filter(Q(name__icontains=term) | Q(symbol__icontains=term)).order_by("symbol")
        response = [[gene.id, gene.symbol, gene.name] for gene in genes]

        return HttpResponse(json.dumps(response), mimetype="application/json")


class VariationInline(admin.TabularInline):
    model = Variation
    form = VariationForm
    raw_id_fields = ("gene",)
    extra = 2
    max_num = 100
    exclude = (
        "exon_validation_override",
        "dna_variation_validation_override",
        "rna_variation_validation_override",
        "protein_variation_validation_override",
    )
    formfield_overrides = {
        models.TextField: {"widget": django.forms.TextInput},
    }



class MolecularDataAdmin(admin.ModelAdmin):
    actions = None
    add_form_template = "templates/admin/genetic/change_form.html"
    change_form_template = "templates/admin/genetic/change_form.html"
    form = MolecularDataForm
    inlines = [
        VariationInline,
    ]
    search_fields = ["patient__family_name", "patient__given_names"]
    #FJ added 'working group' field
    # Trac #32 added moleculardata_entered
    list_display = ['patient_name', 'patient_working_group', 'moleculardata_entered']

    def patient_name(self, obj):
        return ("%s") % (obj.patient, )

    def patient_working_group(self, obj):
        return ("%s") % (obj.patient.working_group, )

    patient_name.short_description = 'Name'
    patient_working_group.short_description = 'Working Group'

    def get_urls(self):
        urls = super(MolecularDataAdmin, self).get_urls()
        local_urls = patterns("",
            (r"override/(?P<type>(exon)|([dr]na)|(protein))/(?P<id>\d+)$", self.admin_site.admin_view(self.override_validation)),
            (r"validate/exon$", self.admin_site.admin_view(self.validate_exon)),
            (r"validate/protein$", self.admin_site.admin_view(self.validate_protein)),
            (r"validate/sequence$", self.admin_site.admin_view(self.validate_sequence)),
        )
        #print 'urls: ', local_urls + urls
        return local_urls + urls

    def override_validation(self, request, type, id):
        #print 'override_validation happening'
        variation = get_object_or_404(Variation, pk=int(id))

        if not request.user.has_perm("genetic.can_override_validation"):
            return HttpResponseForbidden(json.dumps("User cannot override variation validation"), mimetype="application/json")

        try:
            variation.set_validation_override(type)
            variation.save()
        except KeyError:
            return HttpResponseBadRequest(json.dumps("Invalid variation type"), mimetype="application/json")

        return HttpResponse(status=204)

    def queryset(self, request):
        import registry.groups.models

        if request.user.is_superuser:
            return MolecularData.objects.all()

        user = registry.groups.models.User.objects.get(user=request.user)

        if self.has_change_permission(request):
            return MolecularData.objects.filter(patient__working_group=user.working_group).filter(patient__active=True)
        else:
            return MolecularData.objects.none()

    def validate_exon(self, request):
        #print 'validating exon'
        from registry.humangenome.exon import ExonVariation

        try:
            ExonVariation(request.raw_post_data)
            return HttpResponse(status=204)
        except ExonVariation.Error, e:
            return HttpResponseBadRequest(json.dumps([unicode(e)]), mimetype="application/json")

    def validate_protein(self, request):
        #print 'validating protein'
        from registry.humangenome.protein import ProteinVariation

        try:
            ProteinVariation(request.raw_post_data)
            return HttpResponse(status=204)
        except ProteinVariation.Error, e:
            return HttpResponseBadRequest(json.dumps([unicode(e)]), mimetype="application/json")

    def validate_sequence(self, request):
        #print 'validating sequence'
        from registry.humangenome.sequence import SequenceVariation

        try:
            SequenceVariation(request.raw_post_data)
            return HttpResponse(status=204)
        except SequenceVariation.Error, e:
            return HttpResponseBadRequest(json.dumps([unicode(e)]), mimetype="application/json")

    def moleculardata_entered(self, obj):
        if not hasattr(obj, 'variation_set') or not obj.variation_set.all():
            return ''

        imagefile = 'tick.png'

        #genetic_url = '<a href="%s">' % urlresolvers.reverse('admin:genetic_moleculardata_change', args=(obj.id,))
        #genetic_url += '<img src="%s"/>' % url("/static/images/" + imagefile)
        genetic_url = '<img src="%s"/>' % url("/static/images/" + imagefile)
        #genetic_url += '</a>'
        return genetic_url

    moleculardata_entered.allow_tags = True
    moleculardata_entered.short_description = "Genetic Data"

if settings.INSTALL_NAME == "dm1":
    from registry.dm1.admin import DiagnosticCategoryInline
    MolecularDataAdmin.inlines = [DiagnosticCategoryInline] + MolecularDataAdmin.inlines


admin.site.register(MolecularData, MolecularDataAdmin)
admin.site.register(Gene, GeneAdmin)
