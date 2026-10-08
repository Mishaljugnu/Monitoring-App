from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TelemetrySample(Base):
    __tablename__ = "telemetry_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    internet_status: Mapped[str] = mapped_column(String(16))
    download_speed_mbps: Mapped[float] = mapped_column(Float)
    upload_speed_mbps: Mapped[float] = mapped_column(Float)
    bandwidth_usage_percent: Mapped[float] = mapped_column(Float)
    throughput_mbps: Mapped[float] = mapped_column(Float)
    ping_ms: Mapped[float] = mapped_column(Float)
    latency_ms: Mapped[float] = mapped_column(Float)
    jitter_ms: Mapped[float] = mapped_column(Float)
    packet_loss_percent: Mapped[float] = mapped_column(Float)
    cpu_usage_percent: Mapped[float] = mapped_column(Float)
    ram_usage_percent: Mapped[float] = mapped_column(Float)
    disk_usage_percent: Mapped[float] = mapped_column(Float)
    network_adapter: Mapped[str] = mapped_column(String(128))
    connection_type: Mapped[str] = mapped_column(String(32))
    public_ip: Mapped[str] = mapped_column(String(64))
    private_ip: Mapped[str] = mapped_column(String(64))
    gateway: Mapped[str] = mapped_column(String(64))
    dns_csv: Mapped[str] = mapped_column(Text)
    mac_address: Mapped[str] = mapped_column(String(64))
    network_uptime_seconds: Mapped[float] = mapped_column(Float)
    isp: Mapped[str] = mapped_column(String(128))


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(16))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class AIRecommendationRecord(Base):
    __tablename__ = "ai_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recommendation_id: Mapped[str] = mapped_column(String(128), index=True)
    problem_summary: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    confidence_score: Mapped[int] = mapped_column(Integer)
    possible_cause: Mapped[str] = mapped_column(Text)
    technical_explanation: Mapped[str] = mapped_column(Text)
    recommended_fixes_json: Mapped[str] = mapped_column(Text)
    estimated_improvement: Mapped[str] = mapped_column(Text)
    priority_level: Mapped[str] = mapped_column(String(16))
    supporting_metrics_json: Mapped[str] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class PredictionRecordEntity(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    metric: Mapped[str] = mapped_column(String(64), index=True)
    horizon: Mapped[str] = mapped_column(String(64))
    predicted_value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(16))
    confidence_score: Mapped[int] = mapped_column(Integer)
    interpretation: Mapped[str] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(DateTime, index=True)
