from pydantic import BaseModel, Field
class VolumeRequest(BaseModel):
    voxel_count:int=Field(ge=0); spacing_mm:tuple[float,float,float]
class MetricsRequest(BaseModel): prediction:list; reference:list
class MockRequest(BaseModel): shape:tuple[int,int,int]; spacing_mm:tuple[float,float,float]=(1,1,1)

