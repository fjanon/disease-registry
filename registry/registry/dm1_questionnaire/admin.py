# -*- coding: utf-8 -*-
from django.contrib import admin
from django.conf.urls.defaults import patterns
from django.db import transaction
from django.http import HttpResponseRedirect
from admin_forms import *
from models import *


class MotorFunctionInline(admin.StackedInline):
    model = MotorFunction

class SurgeryInline(admin.StackedInline):
    model = Surgery

class RespiratoryInline(admin.StackedInline):
    form = RespiratoryForm
    model = Respiratory

class FeedingFunctionInline(admin.StackedInline):
    model = FeedingFunction

class ClinicalTrialsInline(admin.TabularInline):
    model = ClinicalTrials
    extra = 3

class HeartMedicationInline(admin.TabularInline):
    model = HeartMedication
    extra = 3

class HeartInline(admin.StackedInline):
    form = HeartForm
    model = Heart

class MuscleMedicationInline(admin.TabularInline):
    model = MuscleMedication
    extra = 3

class MuscleInline(admin.StackedInline):
    model = Muscle

class FatigueInline(admin.StackedInline):
    model = Fatigue

class FatigueMedicationInline(admin.TabularInline):
    model = FatigueMedication
    extra = 3

class SocioeconomicFactorsInline(admin.StackedInline):
    model = SocioeconomicFactors

class GeneralMedicalFactorsInline(admin.StackedInline):
    model = GeneralMedicalFactors

class GeneticTestDetailsInline(admin.StackedInline):
    form = GeneticTestDetailsForm
    model = GeneticTestDetails

class EthnicOriginInline(admin.StackedInline):
    model = EthnicOrigin

class FamilyMemberInline(admin.TabularInline):
    model = FamilyMember
    extra = 3

class ConsentInline(admin.StackedInline):
    model = Consent

class DiagnosisAdmin(admin.ModelAdmin):
    actions = None
    form = DiagnosisForm
    inlines = [
        MotorFunctionInline,
        MuscleInline,
        MuscleMedicationInline,
        SurgeryInline,
        HeartInline,
        HeartMedicationInline,
        RespiratoryInline,
        FeedingFunctionInline,
        FatigueInline,
        FatigueMedicationInline,
        SocioeconomicFactorsInline,
        GeneralMedicalFactorsInline,
        GeneticTestDetailsInline,
        EthnicOriginInline,
        ClinicalTrialsInline,
        FamilyMemberInline,
        ConsentInline,
    ]
    search_fields = ["patient__family_name", "patient__given_names"]
    # FJ start Trac 16 Item 10, reordering fields, patient first
    fields = ('patient', 'first_symptom', 'first_suspected_by', 'age_at_clinical_diagnosis', 'age_at_molecular_diagnosis')
    # FJ end

    class Media:
        from ccg.utils.webhelpers import url

        css = {
            "screen": [url("/static/css/diagnosis_admin.css")]
        }

    def queryset(self, request):
        import registry.groups.models

        if request.user.is_superuser:
            return Diagnosis.objects.all()

        user = groups.models.User.objects.get(user=request.user)

        if self.has_change_permission(request):
            return Diagnosis.objects.filter(patient__working_group=user.working_group)   #.filter(patient__active=True)   QUICK ISSUE FIX
        else:
            return Diagnosis.objects.none()


class PatientAdmin(admin.ModelAdmin):
    actions = ["approve_action"]
    list_display = ["__unicode__", "diagnosis_link", "approve"]
    form = PatientForm

    def get_urls(self):
        urls = super(PatientAdmin, self).get_urls()
        patient_urls = patterns("",
            (r"^approve/(\d+)/", self.admin_site.admin_view(self.approve_view)),
        )
        return patient_urls + urls

    # Admin actions.
    @transaction.commit_on_success()
    def approve_action(self, request, qs):
        count = qs.count()

        for patient in qs:
            patient.approve()

        self.message_user(request, "%d patient(s) approved" % count)
    approve_action.short_description = "Approve selected patient(s)"

    # Admin list cells.
    def approve(self, patient):
        return "<a href='approve/%d/'>Approve</a>" % patient.pk
    approve.allow_tags = True

    def diagnosis_link(self, patient):
        return "<a href='../diagnosis/%d/'>Diagnosis</a>" % patient.diagnosis.pk
    diagnosis_link.allow_tags = True
    diagnosis_link.short_description = "Diagnosis"

    # Admin views.
    @transaction.commit_on_success()
    def approve_view(self, request, id):
        patient = Patient.objects.get(pk=id)
        name = unicode(patient)
        patient.approve()

        self.message_user(request, "Patient %s approved" % name)
        return HttpResponseRedirect("../../")


admin.site.register(Diagnosis, DiagnosisAdmin)
admin.site.register(Patient, PatientAdmin)
