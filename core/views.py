import io, time
import numpy as np
import nibabel as nib
from PIL import Image
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import MedicalImageForm, ProjectForm, ReviewForm
from .models import AnalysisResult, MedicalImage, ModelVersion, Project, Review, Role
from .permissions import roles_required
from .services import audit, build_ra_report, calculate_volume_cm3, segmentation_metrics

@login_required
def dashboard(request):
    return render(request,"core/dashboard.html",{"projects":Project.objects.prefetch_related("images__analyses").order_by("-created_at")})

@roles_required(Role.ANALYST,Role.ADMIN)
def project_create(request):
    form=ProjectForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        obj=form.save(commit=False); obj.created_by=request.user; obj.save(); audit(request.user,"PROJECT_CREATED",obj); return redirect("project_detail",pk=obj.pk)
    return render(request,"core/form.html",{"form":form,"title":"프로젝트 생성"})

@login_required
def project_detail(request,pk):
    project=get_object_or_404(Project.objects.prefetch_related("images__analyses__reviews","documents"),pk=pk)
    return render(request,"core/project_detail.html",{"project":project,"upload_form":MedicalImageForm()})

@roles_required(Role.ANALYST,Role.ADMIN)
def image_upload(request,pk):
    project=get_object_or_404(Project,pk=pk); form=MedicalImageForm(request.POST,request.FILES)
    if form.is_valid():
        obj=form.save(commit=False); obj.project=project; obj.uploaded_by=request.user; obj.save(); audit(request.user,"IMAGE_UPLOADED",obj,{"modality":obj.modality}); messages.success(request,"영상이 등록되었습니다.")
    else:
        messages.error(request," ".join(sum(form.errors.values(),[])))
    return redirect("project_detail",pk=pk)

def _png_overlay(volume,mask):
    z=volume.shape[2]//2; img=np.nan_to_num(volume[:,:,z]); img=(255*(img-img.min())/(np.ptp(img) or 1)).astype(np.uint8)
    rgb=np.stack([img,img,img],axis=-1); m=mask[:,:,z]
    rgb[m,0]=255; rgb[m,1]=(rgb[m,1]*.35).astype(np.uint8); rgb[m,2]=(rgb[m,2]*.35).astype(np.uint8)
    out=io.BytesIO(); Image.fromarray(np.rot90(rgb)).save(out,"PNG"); return out.getvalue()

@roles_required(Role.ANALYST,Role.ADMIN)
@require_POST
def run_analysis(request,image_id):
    image=get_object_or_404(MedicalImage,pk=image_id); model=get_object_or_404(ModelVersion,pk=request.POST.get("model_version"),active=True)
    result=AnalysisResult.objects.create(image=image,model_version=model,created_by=request.user,status=AnalysisResult.Status.RUNNING)
    audit(request.user,"ANALYSIS_STARTED",result)
    started=time.perf_counter()
    try:
        source=nib.load(image.file.path); data=np.asarray(source.dataobj,dtype=np.float32)
        if data.ndim!=3: raise ValueError("3차원 NIfTI만 지원합니다.")
        threshold=float(np.percentile(data,85)); mask=data>threshold
        spacing=tuple(float(x) for x in source.header.get_zooms()[:3]); count=int(mask.sum())
        result.voxel_count=count; result.spacing_x,result.spacing_y,result.spacing_z=spacing; result.volume_cm3=calculate_volume_cm3(count,spacing)
        mask_img=nib.Nifti1Image(mask.astype(np.uint8),source.affine,source.header)
        result.mask_file.save("mock_mask.nii",ContentFile(mask_img.to_bytes()),save=False)
        result.overlay_file.save("overlay.png",ContentFile(_png_overlay(data,mask)),save=False)
        if image.reference_mask:
            ref=np.asarray(nib.load(image.reference_mask.path).dataobj)>0
            values=segmentation_metrics(mask,ref)
            for key,value in values.items(): setattr(result,key,value)
        result.status=AnalysisResult.Status.COMPLETED
    except Exception as exc:
        result.status=AnalysisResult.Status.FAILED; result.error_message=str(exc)[:2000]
    result.execution_seconds=time.perf_counter()-started; result.save(); audit(request.user,"ANALYSIS_FINISHED",result,{"status":result.status})
    return redirect("analysis_detail",pk=result.pk)

@login_required
def analysis_detail(request,pk):
    result=get_object_or_404(AnalysisResult.objects.select_related("image__project","model_version"),pk=pk)
    return render(request,"core/analysis_detail.html",{"result":result,"review_form":ReviewForm()})

@roles_required(Role.REVIEWER,Role.ADMIN)
@require_POST
def review_analysis(request,pk):
    result=get_object_or_404(AnalysisResult,pk=pk)
    if result.status!=AnalysisResult.Status.COMPLETED or result.is_locked:
        messages.error(request,"완료된 미승인 결과만 검토할 수 있습니다."); return redirect("analysis_detail",pk=pk)
    form=ReviewForm(request.POST)
    if form.is_valid():
        review=form.save(commit=False); review.analysis=result; review.reviewer=request.user; review.save(); audit(request.user,"ANALYSIS_REVIEWED",result,{"decision":review.decision,"comment":review.comment})
    else: messages.error(request,"검토 입력을 확인하세요.")
    return redirect("analysis_detail",pk=pk)

@roles_required(Role.REVIEWER,Role.ADMIN)
@require_POST
def generate_report(request,pk):
    project=get_object_or_404(Project,pk=pk)
    if not Review.objects.filter(analysis__image__project=project,decision=Review.Decision.APPROVED).exists():
        messages.error(request,"승인된 분석 결과가 있어야 보고서를 생성할 수 있습니다."); return redirect("project_detail",pk=pk)
    record=build_ra_report(project,request.user); return redirect("download_report",pk=record.pk)

@login_required
def download_report(request,pk):
    from .models import GeneratedDocument
    document=get_object_or_404(GeneratedDocument,pk=pk)
    if not document.file: raise Http404
    return FileResponse(document.file.open("rb"),as_attachment=True,filename=document.file.name.rsplit("/",1)[-1])
