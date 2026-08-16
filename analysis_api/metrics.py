import numpy as np

def volume_cm3(voxel_count: int, spacing_mm: tuple[float,float,float]) -> float:
    return float(voxel_count * np.prod(spacing_mm) / 1000.0)

def metrics(pred, ref):
    pred=np.asarray(pred,dtype=bool); ref=np.asarray(ref,dtype=bool)
    if pred.shape != ref.shape: raise ValueError("shape mismatch")
    tp=np.logical_and(pred,ref).sum(); fp=np.logical_and(pred,~ref).sum(); fn=np.logical_and(~pred,ref).sum()
    return {"dice":float(2*tp/(2*tp+fp+fn)) if 2*tp+fp+fn else 1.0,
            "iou":float(tp/(tp+fp+fn)) if tp+fp+fn else 1.0,
            "sensitivity":float(tp/(tp+fn)) if tp+fn else 1.0,
            "precision":float(tp/(tp+fp)) if tp+fp else 1.0}

