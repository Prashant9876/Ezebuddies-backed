from typing import Any

from pydantic import BaseModel, Field


class HistoricalRange(BaseModel):
    value: float = Field(gt=0)


class HistoricalDataRequest(BaseModel):
    user_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    device_name: str = Field(min_length=1)
    time_range: HistoricalRange


class HistoricalDataPoint(BaseModel):
    timestamp: str
    payload: dict[str, Any]


class HistoricalDataResponse(BaseModel):
    user_id: str
    device_id: str
    device_name: str
    time_range_days: float
    bucket_minutes: int
    total_points: int
    data: list[HistoricalDataPoint]
