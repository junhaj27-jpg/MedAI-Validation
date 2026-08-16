import uuid
from pathlib import Path
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

class Role(models.TextChoices):
    ANALYST = "ANALYST", "분석자"
    REVIEWER = "REVIEWER", "검토자"
    ADMIN = "ADMIN", "관리자"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.ANALYST)

def upload_path(instance, filename):
    name = filename.lower()
    suffix = ".nii.gz" if name.endswith(".nii.gz") else ".nii"
    project_id = getattr(instance, "project_id", None) or instance.image.project_id
    return f"studies/{project_id}/{uuid.uuid4()}{suffix}"

class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="projects")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return self.name

class MedicalImage(models.Model):
    class Modality(models.TextChoices): MRI = "MRI", "MRI"; CT = "CT", "CT"
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="images")
    file = models.FileField(upload_to=upload_path)
    reference_mask = models.FileField(upload_to=upload_path, blank=True)
    study_date = models.DateField()
    modality = models.CharField(max_length=3, choices=Modality.choices)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

class ModelVersion(models.Model):
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: constraints = [models.UniqueConstraint(fields=["name", "version"], name="unique_model_version")]
    def __str__(self): return f"{self.name} {self.version}"

class AnalysisResult(models.Model):
    class Status(models.TextChoices):
        PENDING="PENDING","대기"; RUNNING="RUNNING","실행 중"; COMPLETED="COMPLETED","완료"; FAILED="FAILED","실패"
    image = models.ForeignKey(MedicalImage, on_delete=models.CASCADE, related_name="analyses")
    model_version = models.ForeignKey(ModelVersion, on_delete=models.PROTECT)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    mask_file = models.FileField(upload_to=upload_path, blank=True)
    overlay_file = models.ImageField(upload_to="overlays/%Y/%m/", blank=True)
    voxel_count = models.PositiveBigIntegerField(null=True, blank=True)
    spacing_x = models.FloatField(null=True, blank=True); spacing_y = models.FloatField(null=True, blank=True); spacing_z = models.FloatField(null=True, blank=True)
    volume_cm3 = models.FloatField(null=True, blank=True)
    dice = models.FloatField(null=True, blank=True); iou = models.FloatField(null=True, blank=True)
    sensitivity = models.FloatField(null=True, blank=True); precision = models.FloatField(null=True, blank=True)
    execution_seconds = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True); updated_at = models.DateTimeField(auto_now=True)
    @property
    def is_locked(self): return self.reviews.filter(decision=Review.Decision.APPROVED).exists()
    def save(self, *args, **kwargs):
        if self.pk and AnalysisResult.objects.filter(pk=self.pk, reviews__decision="APPROVED").exists():
            old = AnalysisResult.objects.get(pk=self.pk)
            editable = ["status","mask_file","voxel_count","spacing_x","spacing_y","spacing_z","volume_cm3","dice","iou","sensitivity","precision","model_version_id"]
            if any(getattr(old, f) != getattr(self, f) for f in editable):
                raise ValidationError("승인된 분석 결과는 수정할 수 없습니다.")
        super().save(*args, **kwargs)

class Review(models.Model):
    class Decision(models.TextChoices): APPROVED="APPROVED","승인"; REJECTED="REJECTED","반려"
    analysis = models.ForeignKey(AnalysisResult, on_delete=models.CASCADE, related_name="reviews")
    reviewer = models.ForeignKey(User, on_delete=models.PROTECT)
    decision = models.CharField(max_length=10, choices=Decision.choices)
    comment = models.TextField()
    reviewed_at = models.DateTimeField(auto_now_add=True)

class GeneratedDocument(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to="reports/%Y/%m/")
    generated_by = models.ForeignKey(User, on_delete=models.PROTECT)
    generated_at = models.DateTimeField(auto_now_add=True)

class AuditLog(models.Model):
    actor = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    detail = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]
