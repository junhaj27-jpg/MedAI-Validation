from django.contrib import admin
from .models import AuditLog,GeneratedDocument,MedicalImage,ModelVersion,Profile,Project,Review,AnalysisResult
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin): list_display=("user","role"); list_filter=("role",)
@admin.register(ModelVersion)
class ModelVersionAdmin(admin.ModelAdmin): list_display=("name","version","active"); list_filter=("active",)
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin): list_display=("created_at","actor","action","object_type","object_id"); readonly_fields=("actor","action","object_type","object_id","detail","created_at")
    
admin.site.register([Project,MedicalImage,AnalysisResult,Review,GeneratedDocument])

