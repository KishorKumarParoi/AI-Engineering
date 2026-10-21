from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class MobileFeatures(BaseModel):
    battery_power: int = Field(..., ge=500, le=2000, description="Total energy a battery can store in mAh", examples=[842])
    blue: int = Field(..., ge=0, le=1, description="Has bluetooth or not (0=No, 1=Yes)", examples=[0])
    clock_speed: float = Field(..., ge=0.5, le=3.0, description="Speed at which microprocessor executes instructions", examples=[2.2])
    dual_sim: int = Field(..., ge=0, le=1, description="Has dual sim support or not (0=No, 1=Yes)", examples=[0])
    fc: int = Field(..., ge=0, le=20, description="Front Camera mega pixels", examples=[1])
    four_g: int = Field(..., ge=0, le=1, description="Has 4G or not (0=No, 1=Yes)", examples=[0])
    int_memory: int = Field(..., ge=2, le=64, description="Internal Memory in Gigabytes", examples=[7])
    m_dep: float = Field(..., ge=0.1, le=1.0, description="Mobile Depth in cm", examples=[0.6])
    mobile_wt: int = Field(..., ge=80, le=200, description="Weight of mobile phone in grams", examples=[188])
    n_cores: int = Field(..., ge=1, le=8, description="Number of cores of processor", examples=[2])
    pc: int = Field(..., ge=0, le=20, description="Primary Camera mega pixels", examples=[2])
    px_height: int = Field(..., ge=0, le=1960, description="Pixel Resolution Height", examples=[20])
    px_width: int = Field(..., ge=500, le=1998, description="Pixel Resolution Width", examples=[756])
    ram: int = Field(..., ge=256, le=3998, description="Random Access Memory in Megabytes", examples=[2549])
    sc_h: int = Field(..., ge=5, le=19, description="Screen Height of mobile in cm", examples=[9])
    sc_w: int = Field(..., ge=0, le=18, description="Screen Width of mobile in cm", examples=[7])
    talk_time: int = Field(..., ge=2, le=20, description="Longest time that a single battery charge will last", examples=[19])
    three_g: int = Field(..., ge=0, le=1, description="Has 3G or not (0=No, 1=Yes)", examples=[0])
    touch_screen: int = Field(..., ge=0, le=1, description="Has touch screen or not (0=No, 1=Yes)", examples=[0])
    wifi: int = Field(..., ge=0, le=1, description="Has wifi or not (0=No, 1=Yes)", examples=[1])


class PredictionRequest(BaseModel):
    instances: List[MobileFeatures] = Field(
        ...,
        description="List of mobile specification items for batch or single inference",
    )


class PredictionItem(BaseModel):
    index: int
    predicted_class: int = Field(..., description="Target class integer (0, 1, 2, or 3)")
    predicted_label: str = Field(..., description="Human readable label (Low Cost, Medium Cost, High Cost, Very High Cost)")
    confidence: float = Field(..., description="Confidence probability for the predicted class")
    probabilities: Dict[str, float] = Field(..., description="Probabilities for each of the 4 classes")


class PredictionResponse(BaseModel):
    predictions: List[PredictionItem]
    classes: List[int]
    labels: List[str]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_type: str
    feature_count: int
    features: List[str]
    target_classes: Dict[str, str]
