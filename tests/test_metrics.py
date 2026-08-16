import numpy as np
import pytest
from core.services import calculate_volume_cm3, segmentation_metrics

def test_volume_converts_mm3_to_cm3():
    assert calculate_volume_cm3(1000,(1.0,1.0,2.0)) == pytest.approx(2.0)

def test_dice_and_iou_known_arrays():
    pred=np.array([1,1,0,0]); ref=np.array([1,0,1,0])
    result=segmentation_metrics(pred,ref)
    assert result["dice"]==pytest.approx(0.5); assert result["iou"]==pytest.approx(1/3)
    assert result["sensitivity"]==pytest.approx(0.5); assert result["precision"]==pytest.approx(0.5)

def test_empty_masks_are_perfect_match():
    result=segmentation_metrics(np.zeros(3),np.zeros(3)); assert result=={"dice":1.0,"iou":1.0,"sensitivity":1.0,"precision":1.0}

