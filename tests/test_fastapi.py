import pytest
from fastapi.testclient import TestClient
from analysis_api.main import app
client=TestClient(app)
def test_swagger_available(): assert client.get("/docs").status_code==200
def test_volume_endpoint():
    response=client.post("/volume",json={"voxel_count":500,"spacing_mm":[1,2,3]})
    assert response.status_code==200; assert response.json()["volume_cm3"]==pytest.approx(3.0)
def test_metrics_endpoint():
    response=client.post("/metrics",json={"prediction":[1,1,0],"reference":[1,0,0]})
    assert response.status_code==200; assert response.json()["dice"]==pytest.approx(2/3)

