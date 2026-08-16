# 의료영상 AI 분석·검증 및 RA 보고서 자동화 플랫폼

익명화된 MRI/CT NIfTI 영상을 등록하고 mock segmentation 결과, 병변 부피, 기준 마스크 대비 성능지표를 검토·승인한 뒤 RA 검증 보고서(DOCX)를 생성하는 포트폴리오 MVP입니다.

> 본 서비스는 연구·포트폴리오용이며 의료진의 진단을 대체하지 않습니다. 실제 환자 데이터나 임상 의사결정에 사용하지 마세요.

## 주요 기능

- `ANALYST`: 프로젝트/영상 등록, mock 분석 실행
- `REVIEWER`: 결과 승인·반려, 보고서 생성
- `ADMIN`: Django Admin에서 사용자, 역할, 모델 버전 관리
- NIfTI `.nii`/`.nii.gz` 확장자·크기 검증, UUID 파일명, 경로 조작 방지
- 중앙 axial slice에 segmentation overlay 표시
- 부피(cm³) = voxel 수 × spacing x/y/z(mm) ÷ 1000
- Dice, IoU, 민감도, 정밀도 계산과 표/그래프 표시
- 승인 이후 핵심 결과 수정 차단 및 변경 AuditLog
- 프로젝트/모델/입력/결과/지표/검토 이력/한계를 담은 DOCX
- FastAPI Swagger: `/docs`

## 빠른 실행 (Docker/PostgreSQL)

```bash
cp .env.example .env
docker compose up --build
docker compose exec web python manage.py createsuperuser
```

Django는 `http://localhost:8000`, Django Admin은 `/admin/`, FastAPI Swagger는 `http://localhost:8001/docs`입니다. Admin에서 사용자별 `Profile`과 `ModelVersion`을 먼저 생성하세요.

## 로컬 개발

Python 3.12 및 PostgreSQL을 권장합니다. `DATABASE_URL`을 설정하지 않으면 개발·테스트 편의를 위해 SQLite를 사용합니다.

```bash
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
uvicorn analysis_api.main:app --reload --port 8001
```

## 데모 흐름

1. Admin에서 분석자/검토자 계정과 Profile 역할, 활성 모델 버전을 만든다.
2. 분석자로 로그인하여 프로젝트를 만들고 익명화된 NIfTI와 선택적 기준 마스크를 등록한다.
3. 모델 버전 ID를 선택해 mock 분석을 실행하고 overlay, 부피, 지표를 확인한다.
4. 검토자로 로그인하여 완료 결과를 승인 또는 반려한다.
5. 프로젝트에서 DOCX 보고서를 생성·다운로드한다.

## 테스트

```bash
pytest
```

테스트는 실제 의료영상 파일을 포함하지 않으며 작은 NumPy 배열과 DB fixture만 사용합니다.

## 구조

```text
config/          Django 설정/URL
core/            모델, 폼, 권한, 업무 서비스, 화면
analysis_api/    FastAPI mock inference 및 지표 API
templates/       Bootstrap 기반 Django Template
static/          화면 스타일
tests/           계산, API, 권한, 승인 잠금, 보고서 테스트
media/           런타임 업로드(버전관리 제외)
```

## 보안 및 개인정보

환자 이름, 생년월일, 병원번호 입력 필드를 제공하지 않습니다. 업로드는 허용된 확장자와 제한 크기를 검사하고 서버 저장명은 UUID로 변경합니다. `.gitignore`는 NIfTI, DICOM, 모델 가중치, 업로드 및 생성 보고서를 제외합니다. 운영 환경에서는 HTTPS, 악성 파일 검사, 객체 저장소, 비동기 작업 큐, 데이터 보존/삭제 정책과 조직별 접근통제를 추가해야 합니다.

## MVP 한계

- 실제 학습 모델 대신 영상 강도 85 percentile 기반 mock segmentation을 사용합니다.
- 3차원 NIfTI만 지원하며 고급 viewer, DICOM, 다중 병변 편집은 포함하지 않습니다.
- PDF 변환은 OS별 LibreOffice 의존성을 피하기 위해 제외하고 DOCX를 제공합니다.
- FastAPI 계산 API와 Django 업무 흐름은 독립 배포 가능하나, MVP의 NIfTI 파일 분석 실행은 Django 프로세스에서 수행합니다.
- 임상 성능, 규제 적합성, 의료기기 허가를 보장하지 않습니다.
