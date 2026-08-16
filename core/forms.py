from pathlib import Path
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import MedicalImage, Project, Review

def validate_nifti(value):
    name = value.name.lower()
    if not (name.endswith(".nii") or name.endswith(".nii.gz")):
        raise ValidationError("NIfTI 파일(.nii, .nii.gz)만 업로드할 수 있습니다.")
    if value.size > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise ValidationError(f"파일 크기는 {settings.MAX_UPLOAD_MB}MB 이하여야 합니다.")
    if Path(value.name).name != value.name.replace("\\", "/").split("/")[-1]:
        raise ValidationError("유효하지 않은 파일명입니다.")

class ProjectForm(forms.ModelForm):
    class Meta: model = Project; fields = ["name", "description"]

class MedicalImageForm(forms.ModelForm):
    class Meta: model = MedicalImage; fields = ["file", "reference_mask", "study_date", "modality", "description"]; widgets = {"study_date": forms.DateInput(attrs={"type":"date"})}
    def clean_file(self): value=self.cleaned_data["file"]; validate_nifti(value); return value
    def clean_reference_mask(self):
        value=self.cleaned_data.get("reference_mask")
        if value: validate_nifti(value)
        return value

class ReviewForm(forms.ModelForm):
    class Meta: model = Review; fields = ["decision", "comment"]

