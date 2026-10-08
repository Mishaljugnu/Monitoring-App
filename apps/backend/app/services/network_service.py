import asyncio
import time
from collections import deque
from datetime import datetime, timezone
from typing import Optional

import httpx
import os
import psutil
from ping3 import ping

from app.core.config import settings
from app.schemas import TelemetrySnapshot
from app.services.host_network_service import HostNetworkService


class NetworkCollector:
    def __init__(self, host_network_service: HostNetworkService) -> None:
        self._host_network_service = host_network_service
        self._last_counters: Optional[tuple[float, float, float]] = None
        self._latency_window: deque[float] = deque(maxlen=12)
        self._public_ip: str = "Unknown"
        self._isp: str = "Unknown"
        self._last_external_lookup: float = 0.0

    async def collect(self) -> TelemetrySnapshot:
        context = self._host_network_service.get_primary_interface()
        io_counters = psutil.net_io_counters(pernic=True)
        pernic = io_counters.get(context.name) if io_counters else None
        download_speed_mbps = 0.0
        upload_speed_mbps = 0.0

        now = time.monotonic()
        if pernic:
            if self._last_counters:
                previous_ts, previous_recv, previous_sent = self._last_counters
                elapsed = max(now - previous_ts, 0.001)
                download_speed_mbps = max(((pernic.bytes_recv - previous_recv) * 8) / elapsed / 1_000_000, 0.0)
                upload_speed_mbps = max(((pernic.bytes_sent - previous_sent) * 8) / elapsed / 1_000_000, 0.0)
            self._last_counters = (now, float(pernic.bytes_recv), float(pernic.bytes_sent))

        ping_results = await self._probe_latency()
        successful = [value for value in ping_results if value is not None]
        packet_loss_percent = round(((len(ping_results) - len(successful)) / len(ping_results)) * 100, 2)
        latency_ms = round(sum(successful) / len(successful), 2) if successful else 0.0
        ping_ms = latency_ms
        self._latency_window.append(latency_ms if successful else 0.0)
        jitter_ms = self._compute_jitter()

        cpu_usage_percent = psutil.cpu_percent(interval=None)
        ram_usage_percent = psutil.virtual_memory().percent
        disk_usage_percent = psutil.disk_usage(os.path.abspath(os.sep)).percent
        throughput_mbps = round(download_speed_mbps + upload_speed_mbps, 2)
        bandwidth_usage_percent = 0.0
        if context.nominal_speed_mbps > 0:
            bandwidth_usage_percent = round(min((throughput_mbps / context.nominal_speed_mbps) * 100, 100.0), 2)

        await self._refresh_public_network_identity()
        internet_status = self._derive_status(packet_loss_percent, latency_ms)

        return TelemetrySnapshot(
            timestamp=datetime.now(timezone.utc),
            internet_status=internet_status,
            download_speed_mbps=round(download_speed_mbps, 2),
            upload_speed_mbps=round(upload_speed_mbps, 2),
            bandwidth_usage_percent=bandwidth_usage_percent,
            throughput_mbps=throughput_mbps,
            ping_ms=ping_ms,
            latency_ms=latency_ms,
            jitter_ms=jitter_ms,
            packet_loss_percent=packet_loss_percent,
            cpu_usage_percent=round(cpu_usage_percent, 2),
            ram_usage_percent=round(ram_usage_percent, 2),
            disk_usage_percent=round(disk_usage_percent, 2),
            network_adapter=context.name,
            connection_type=context.connection_type,
            public_ip=self._public_ip,
            private_ip=context.private_ip,
            gateway=context.gateway,
            dns=context.dns,
            mac_address=context.mac_address,
            network_uptime_seconds=round(time.time() - psutil.boot_time(), 2),
            isp=self._isp,
        )

    async def _probe_latency(self) -> list[Optional[float]]:
        async def do_ping() -> Optional[float]:
            result = await asyncio.to_thread(ping, "1.1.1.1", timeout=1.5, unit="ms")
            if result is None:
                return None
            return float(result)

        return await asyncio.gather(do_ping(), do_ping(), do_ping())

    def _compute_jitter(self) -> float:
        values = [value for value in self._latency_window if value > 0]
        if len(values) < 2:
            return 0.0
        deltas = [abs(values[index] - values[index - 1]) for index in range(1, len(values))]
        return round(sum(deltas) / len(deltas), 2)

    async def _refresh_public_network_identity(self) -> None:
        if time.time() - self._last_external_lookup < 300:
            return

        try:
            async with httpx.AsyncClient(timeout=settings.public_ip_timeout_seconds) as client:
                response = await client.get("https://ipwho.is/")
                response.raise_for_status()
                payload = response.json()
                if payload.get("success", True):
                    self._public_ip = str(payload.get("ip", "Unknown"))
                    self._isp = str(payload.get("connection", {}).get("isp", "Unknown"))
                    self._last_external_lookup = time.time()
        except Exception:
            pass

    def _derive_status(self, packet_loss_percent: float, latency_ms: float) -> str:
        if packet_loss_percent >= 100:
            return "offline"
        if packet_loss_percent > 5 or latency_ms > 120:
            return "degraded"
        return "online"
