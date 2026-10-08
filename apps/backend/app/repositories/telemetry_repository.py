import json
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AIRecommendationRecord, Alert, PredictionRecordEntity, TelemetrySample
from app.schemas import AIAnalysisPayload, AIRecommendation, AlertRecord, PredictionRecord, TelemetrySnapshot


def _to_snapshot(entity: TelemetrySample) -> TelemetrySnapshot:
    return TelemetrySnapshot(
        timestamp=entity.timestamp,
        internet_status=entity.internet_status,
        download_speed_mbps=entity.download_speed_mbps,
        upload_speed_mbps=entity.upload_speed_mbps,
        bandwidth_usage_percent=entity.bandwidth_usage_percent,
        throughput_mbps=entity.throughput_mbps,
        ping_ms=entity.ping_ms,
        latency_ms=entity.latency_ms,
        jitter_ms=entity.jitter_ms,
        packet_loss_percent=entity.packet_loss_percent,
        cpu_usage_percent=entity.cpu_usage_percent,
        ram_usage_percent=entity.ram_usage_percent,
        disk_usage_percent=entity.disk_usage_percent,
        network_adapter=entity.network_adapter,
        connection_type=entity.connection_type,
        public_ip=entity.public_ip,
        private_ip=entity.private_ip,
        gateway=entity.gateway,
        dns=[value for value in entity.dns_csv.split(",") if value],
        mac_address=entity.mac_address,
        network_uptime_seconds=entity.network_uptime_seconds,
        isp=entity.isp,
    )


def _to_alert(entity: Alert) -> AlertRecord:
    return AlertRecord(
        id=entity.id,
        kind=entity.kind,
        severity=entity.severity,
        message=entity.message,
        created_at=entity.created_at,
    )


def _to_recommendation(entity: AIRecommendationRecord) -> AIRecommendation:
    return AIRecommendation(
        id=entity.recommendation_id,
        problem_summary=entity.problem_summary,
        severity=entity.severity,
        confidence_score=entity.confidence_score,
        possible_cause=entity.possible_cause,
        technical_explanation=entity.technical_explanation,
        recommended_fixes=json.loads(entity.recommended_fixes_json),
        estimated_improvement=entity.estimated_improvement,
        priority_level=entity.priority_level,
        supporting_metrics=json.loads(entity.supporting_metrics_json),
    )


def _to_prediction(entity: PredictionRecordEntity) -> PredictionRecord:
    return PredictionRecord(
        metric=entity.metric,
        horizon=entity.horizon,
        predicted_value=entity.predicted_value,
        unit=entity.unit,
        confidence_score=entity.confidence_score,
        interpretation=entity.interpretation,
    )


class TelemetryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_sample(self, snapshot: TelemetrySnapshot) -> None:
        entity = TelemetrySample(
            timestamp=snapshot.timestamp,
            internet_status=snapshot.internet_status,
            download_speed_mbps=snapshot.download_speed_mbps,
            upload_speed_mbps=snapshot.upload_speed_mbps,
            bandwidth_usage_percent=snapshot.bandwidth_usage_percent,
            throughput_mbps=snapshot.throughput_mbps,
            ping_ms=snapshot.ping_ms,
            latency_ms=snapshot.latency_ms,
            jitter_ms=snapshot.jitter_ms,
            packet_loss_percent=snapshot.packet_loss_percent,
            cpu_usage_percent=snapshot.cpu_usage_percent,
            ram_usage_percent=snapshot.ram_usage_percent,
            disk_usage_percent=snapshot.disk_usage_percent,
            network_adapter=snapshot.network_adapter,
            connection_type=snapshot.connection_type,
            public_ip=snapshot.public_ip,
            private_ip=snapshot.private_ip,
            gateway=snapshot.gateway,
            dns_csv=",".join(snapshot.dns),
            mac_address=snapshot.mac_address,
            network_uptime_seconds=snapshot.network_uptime_seconds,
            isp=snapshot.isp,
        )
        self.session.add(entity)
        await self.session.commit()

    async def get_latest(self) -> Optional[TelemetrySnapshot]:
        result = await self.session.execute(
            select(TelemetrySample).order_by(desc(TelemetrySample.timestamp)).limit(1)
        )
        entity = result.scalar_one_or_none()
        return _to_snapshot(entity) if entity else None

    async def get_history(self, limit: int) -> list[TelemetrySnapshot]:
        result = await self.session.execute(
            select(TelemetrySample)
            .order_by(desc(TelemetrySample.timestamp))
            .limit(limit)
        )
        entities = list(result.scalars().all())
        entities.reverse()
        return [_to_snapshot(item) for item in entities]

    async def get_history_range(self, limit: int, offset: int = 0) -> list[TelemetrySnapshot]:
        result = await self.session.execute(
            select(TelemetrySample)
            .order_by(desc(TelemetrySample.timestamp))
            .offset(max(offset, 0))
            .limit(max(min(limit, 5000), 1))
        )
        entities = list(result.scalars().all())
        entities.reverse()
        return [_to_snapshot(item) for item in entities]

    async def prune_samples(self, keep_latest: int) -> None:
        result = await self.session.execute(
            select(TelemetrySample.id)
            .order_by(desc(TelemetrySample.timestamp))
            .offset(keep_latest)
        )
        stale_ids = list(result.scalars().all())
        if stale_ids:
            await self.session.execute(
                delete(TelemetrySample).where(TelemetrySample.id.in_(stale_ids))
            )
            await self.session.commit()

    async def get_recent_alerts(self, limit: int = 25) -> list[AlertRecord]:
        result = await self.session.execute(
            select(Alert).order_by(desc(Alert.created_at)).limit(limit)
        )
        return [_to_alert(item) for item in result.scalars().all()]

    async def add_alert_if_new(
        self,
        *,
        kind: str,
        severity: str,
        message: str,
        dedupe_seconds: int = 60,
    ) -> Optional[AlertRecord]:
        cutoff = datetime.utcnow() - timedelta(seconds=dedupe_seconds)
        result = await self.session.execute(
            select(Alert)
            .where(Alert.kind == kind, Alert.message == message, Alert.created_at >= cutoff)
            .order_by(desc(Alert.created_at))
            .limit(1)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return None

        entity = Alert(
            kind=kind,
            severity=severity,
            message=message,
            created_at=datetime.utcnow(),
        )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return _to_alert(entity)

    async def save_analysis(self, analysis: AIAnalysisPayload) -> None:
        for recommendation in analysis.recommendations:
            self.session.add(
                AIRecommendationRecord(
                    recommendation_id=recommendation.id,
                    problem_summary=recommendation.problem_summary,
                    severity=recommendation.severity,
                    confidence_score=recommendation.confidence_score,
                    possible_cause=recommendation.possible_cause,
                    technical_explanation=recommendation.technical_explanation,
                    recommended_fixes_json=json.dumps(recommendation.recommended_fixes),
                    estimated_improvement=recommendation.estimated_improvement,
                    priority_level=recommendation.priority_level,
                    supporting_metrics_json=json.dumps(recommendation.supporting_metrics),
                    generated_at=analysis.generated_at,
                )
            )

        for prediction in analysis.predictions:
            self.session.add(
                PredictionRecordEntity(
                    metric=prediction.metric,
                    horizon=prediction.horizon,
                    predicted_value=prediction.predicted_value,
                    unit=prediction.unit,
                    confidence_score=prediction.confidence_score,
                    interpretation=prediction.interpretation,
                    generated_at=analysis.generated_at,
                )
            )

        await self.session.commit()
        await self.prune_analysis(keep_latest=200)

    async def get_recent_recommendations(self, limit: int = 25) -> list[AIRecommendation]:
        result = await self.session.execute(
            select(AIRecommendationRecord).order_by(desc(AIRecommendationRecord.generated_at)).limit(limit)
        )
        return [_to_recommendation(item) for item in result.scalars().all()]

    async def get_recent_predictions(self, limit: int = 25) -> list[PredictionRecord]:
        result = await self.session.execute(
            select(PredictionRecordEntity).order_by(desc(PredictionRecordEntity.generated_at)).limit(limit)
        )
        return [_to_prediction(item) for item in result.scalars().all()]

    async def prune_analysis(self, keep_latest: int) -> None:
        recommendation_result = await self.session.execute(
            select(AIRecommendationRecord.id).order_by(desc(AIRecommendationRecord.generated_at)).offset(keep_latest)
        )
        recommendation_ids = list(recommendation_result.scalars().all())
        if recommendation_ids:
            await self.session.execute(
                delete(AIRecommendationRecord).where(AIRecommendationRecord.id.in_(recommendation_ids))
            )

        prediction_result = await self.session.execute(
            select(PredictionRecordEntity.id).order_by(desc(PredictionRecordEntity.generated_at)).offset(keep_latest)
        )
        prediction_ids = list(prediction_result.scalars().all())
        if prediction_ids:
            await self.session.execute(
                delete(PredictionRecordEntity).where(PredictionRecordEntity.id.in_(prediction_ids))
            )

        if recommendation_ids or prediction_ids:
            await self.session.commit()
