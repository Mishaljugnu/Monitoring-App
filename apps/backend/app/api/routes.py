import asyncio

from fastapi import APIRouter, Query, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse

from app.core.database import SessionLocal
from app.repositories.telemetry_repository import TelemetryRepository
from app.runtime import (
    ai_analysis_service,
    ai_chat_service,
    connection_analyzer_service,
    device_discovery_service,
    monitor_runtime,
    process_monitor_service,
    report_service,
)
from app.schemas import AIChatRequest, HistoricalMetricsPayload

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/api/v1/bootstrap")
async def bootstrap():
    return await monitor_runtime.bootstrap()


@router.get("/api/v1/history")
async def history(limit: int = Query(default=240, ge=1, le=5000), offset: int = Query(default=0, ge=0)):
    async with SessionLocal() as session:
        repository = TelemetryRepository(session)
        records = await repository.get_history_range(limit=limit, offset=offset)
    return HistoricalMetricsPayload(history=records)


@router.get("/api/v1/alerts")
async def alerts(limit: int = Query(default=25, ge=1, le=200)):
    async with SessionLocal() as session:
        repository = TelemetryRepository(session)
        return await repository.get_recent_alerts(limit=limit)


@router.get("/api/v1/devices")
async def devices():
    return await device_discovery_service.scan()


@router.get("/api/v1/processes")
async def processes():
    return await process_monitor_service.scan()


@router.get("/api/v1/connections")
async def connections():
    return await connection_analyzer_service.scan()


@router.get("/api/v1/ai/analysis")
async def ai_analysis():
    telemetry = monitor_runtime.latest
    history = monitor_runtime.history
    devices, processes, connections = await asyncio.gather(
        device_discovery_service.scan(),
        process_monitor_service.scan(),
        connection_analyzer_service.scan(),
    )
    analysis = await ai_analysis_service.analyze(
        telemetry=telemetry,
        history=history,
        devices=devices,
        processes=processes,
        connections=connections,
    )
    async with SessionLocal() as session:
        repository = TelemetryRepository(session)
        await repository.save_analysis(analysis)
    return analysis


@router.get("/api/v1/ai/providers")
async def ai_providers():
    return await ai_chat_service.provider_statuses()


@router.post("/api/v1/ai/chat")
async def ai_chat(payload: AIChatRequest):
    telemetry = monitor_runtime.latest
    history = monitor_runtime.history
    devices, processes, connections = await asyncio.gather(
        device_discovery_service.scan(),
        process_monitor_service.scan(),
        connection_analyzer_service.scan(),
    )
    analysis = await ai_analysis_service.analyze(
        telemetry=telemetry,
        history=history,
        devices=devices,
        processes=processes,
        connections=connections,
    )
    return await ai_chat_service.answer(
        message=payload.message,
        telemetry=telemetry,
        devices=devices,
        processes=processes,
        connections=connections,
        analysis=analysis,
        provider=payload.provider,
    )


@router.get("/api/v1/reports/summary")
async def report_summary():
    devices, processes, connections = await asyncio.gather(
        device_discovery_service.scan(),
        process_monitor_service.scan(),
        connection_analyzer_service.scan(),
    )
    analysis = await ai_analysis_service.analyze(
        telemetry=monitor_runtime.latest,
        history=monitor_runtime.history,
        devices=devices,
        processes=processes,
        connections=connections,
    )
    async with SessionLocal() as session:
        repository = TelemetryRepository(session)
        alerts = await repository.get_recent_alerts()
        await repository.save_analysis(analysis)

    return report_service.build_json_report(
        latest=monitor_runtime.latest,
        alerts=alerts,
        recommendations=analysis.recommendations,
        predictions=analysis.predictions,
        device_count=len(devices),
        process_count=len(processes),
        connection_count=len(connections),
    )


@router.get("/api/v1/reports/export")
async def report_export(format: str = Query(default="json", pattern="^(json|csv)$")):
    async with SessionLocal() as session:
        repository = TelemetryRepository(session)
        history_records = await repository.get_history_range(limit=5000)
        alerts = await repository.get_recent_alerts()
        recommendations = await repository.get_recent_recommendations()
        predictions = await repository.get_recent_predictions()

    if format == "csv":
        return PlainTextResponse(
            report_service.telemetry_csv(history_records),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=netvision-telemetry.csv"},
        )

    payload = report_service.build_json_report(
        latest=monitor_runtime.latest,
        alerts=alerts,
        recommendations=recommendations,
        predictions=predictions,
        device_count=len(await device_discovery_service.scan()),
        process_count=len(await process_monitor_service.scan()),
        connection_count=len(await connection_analyzer_service.scan()),
    )
    return Response(
        report_service.json_text(payload),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=netvision-report.json"},
    )


@router.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await monitor_runtime.register(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await monitor_runtime.unregister(websocket)
    except Exception:
        await monitor_runtime.unregister(websocket)
