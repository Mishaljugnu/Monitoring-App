import csv
import io
import json
from datetime import datetime, timezone
from typing import Optional

from app.schemas import AlertRecord, ReportPayload, TelemetrySnapshot


class ReportService:
    def build_json_report(
        self,
        *,
        latest: Optional[TelemetrySnapshot],
        alerts: list[AlertRecord],
        recommendations,
        predictions,
        device_count: int,
        process_count: int,
        connection_count: int,
    ) -> ReportPayload:
        return ReportPayload(
            generated_at=datetime.now(timezone.utc),
            latest=latest,
            alerts=alerts,
            recommendations=recommendations,
            predictions=predictions,
            device_count=device_count,
            process_count=process_count,
            connection_count=connection_count,
        )

    def telemetry_csv(self, history: list[TelemetrySnapshot]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "timestamp",
                "internet_status",
                "download_speed_mbps",
                "upload_speed_mbps",
                "throughput_mbps",
                "bandwidth_usage_percent",
                "latency_ms",
                "jitter_ms",
                "packet_loss_percent",
                "cpu_usage_percent",
                "ram_usage_percent",
                "disk_usage_percent",
                "network_adapter",
                "connection_type",
                "private_ip",
                "public_ip",
                "gateway",
                "dns",
                "isp",
            ]
        )
        for item in history:
            writer.writerow(
                [
                    item.timestamp.isoformat(),
                    item.internet_status,
                    item.download_speed_mbps,
                    item.upload_speed_mbps,
                    item.throughput_mbps,
                    item.bandwidth_usage_percent,
                    item.latency_ms,
                    item.jitter_ms,
                    item.packet_loss_percent,
                    item.cpu_usage_percent,
                    item.ram_usage_percent,
                    item.disk_usage_percent,
                    item.network_adapter,
                    item.connection_type,
                    item.private_ip,
                    item.public_ip,
                    item.gateway,
                    "|".join(item.dns),
                    item.isp,
                ]
            )
        return output.getvalue()

    def json_text(self, payload: ReportPayload) -> str:
        return json.dumps(json.loads(payload.model_dump_json()), indent=2)
