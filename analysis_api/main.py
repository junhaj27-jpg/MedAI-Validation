import numpy as np
from fastapi import FastAPI, HTTPException
from .metrics import metrics, volume_cm3
from .schemas import MetricsRequest, MockRequest, VolumeRequest

app=FastAPI(title="Medical Imaging Analysis API",version="1.0.0",description="연구·포트폴리오용 mock 의료영상 분석 및 성능평가 API")
@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/volume")
def calculate_volume(req:VolumeRequest):
    if any(x<=0 for x in req.spacing_mm): raise HTTPException(422,"spacing은 양수여야 합니다.")
    return {"volume_cm3":volume_cm3(req.voxel_count,req.spacing_mm),"formula":"voxel_count × spacing_x × spacing_y × spacing_z / 1000","unit":"cm³"}
@app.post("/metrics")
def calculate_metrics(req:MetricsRequest):
    try:return metrics(req.prediction,req.reference)|{"unit":"dimensionless"}
    except ValueError as e:raise HTTPException(422,str(e))
@app.post("/mock-inference")
def mock_inference(req:MockRequest):
    if any(x<=0 for x in req.shape) or any(x>512 for x in req.shape): raise HTTPException(422,"shape 범위가 유효하지 않습니다.")
    grid=np.indices(req.shape); center=(np.array(req.shape)-1).reshape(3,1,1,1)/2; radius=max(1,min(req.shape)/6)
    mask=((grid-center)**2).sum(axis=0)<=radius**2; voxels=int(mask.sum())
    return {"voxel_count":voxels,"volume_cm3":volume_cm3(voxels,req.spacing_mm),"mock":True}
