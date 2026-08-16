from datetime import date
from pathlib import Path
import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import override_settings
from docx import Document
from core.models import AnalysisResult,MedicalImage,ModelVersion,Profile,Project,Review,Role
from core.services import build_ra_report

@pytest.fixture
def workflow(db):
    analyst=User.objects.create_user("a"); Profile.objects.create(user=analyst,role=Role.ANALYST)
    reviewer=User.objects.create_user("r"); Profile.objects.create(user=reviewer,role=Role.REVIEWER)
    project=Project.objects.create(name="Brain MRI validation",description="portfolio",created_by=analyst)
    image=MedicalImage.objects.create(project=project,file="studies/fake.nii",study_date=date(2026,1,1),modality="MRI",uploaded_by=analyst)
    model=ModelVersion.objects.create(name="Mock U-Net",version="1.0")
    result=AnalysisResult.objects.create(image=image,model_version=model,status="COMPLETED",voxel_count=1000,spacing_x=1,spacing_y=1,spacing_z=1,volume_cm3=1,dice=.8,iou=.667,sensitivity=.75,precision=.9,created_by=analyst)
    return analyst,reviewer,project,result

@pytest.mark.django_db
def test_approved_result_cannot_be_modified(workflow):
    _,reviewer,_,result=workflow; Review.objects.create(analysis=result,reviewer=reviewer,decision="APPROVED",comment="ok")
    result.volume_cm3=2
    with pytest.raises(ValidationError): result.save()

@pytest.mark.django_db
def test_report_generation_contains_required_sections(workflow,tmp_path):
    analyst,reviewer,project,result=workflow; Review.objects.create(analysis=result,reviewer=reviewer,decision="APPROVED",comment="검증 완료")
    with override_settings(MEDIA_ROOT=tmp_path):
        record=build_ra_report(project,reviewer); assert Path(record.file.path).exists()
        text="\n".join(p.text for p in Document(record.file.path).paragraphs)
        assert "프로젝트 개요" in text; assert "한계와 주의사항" in text; assert "진단을 대체하지 않습니다" in text

