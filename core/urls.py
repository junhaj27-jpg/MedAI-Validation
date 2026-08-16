from django.urls import path
from . import views
urlpatterns=[
 path("",views.dashboard,name="dashboard"),path("projects/new/",views.project_create,name="project_create"),
 path("projects/<int:pk>/",views.project_detail,name="project_detail"),path("projects/<int:pk>/upload/",views.image_upload,name="image_upload"),
 path("images/<int:image_id>/analyze/",views.run_analysis,name="run_analysis"),path("analyses/<int:pk>/",views.analysis_detail,name="analysis_detail"),
 path("analyses/<int:pk>/review/",views.review_analysis,name="review_analysis"),path("projects/<int:pk>/report/",views.generate_report,name="generate_report"),
 path("reports/<int:pk>/download/",views.download_report,name="download_report")]

