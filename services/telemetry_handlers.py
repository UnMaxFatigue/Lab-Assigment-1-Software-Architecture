from typing import Dict, Any


def handle_overheating(event: Dict[str, Any]) -> None:
    controller = event["controller"]
    vehicule = event["vehicule"]
    active_rental = event["active_rental"]
    if controller._handleOverheatingNoLock(vehicule, active_rental):
        event["stop_processing"] = True


def handle_battery_critical(event: Dict[str, Any]) -> None:
    controller = event["controller"]
    vehicule = event["vehicule"]
    active_rental = event["active_rental"]
    if controller._handleBatteryCriticalNoLock(vehicule, active_rental):
        event["stop_processing"] = True


def handle_location_and_regulations(event: Dict[str, Any]) -> None:
    controller = event["controller"]
    vehicule = event["vehicule"]
    active_rental = event["active_rental"]
    new_location = event["new_location"]
    controller._updateLocationAndApplyRegulationsNoLock(vehicule, new_location, active_rental)


def handle_theft_detection(event: Dict[str, Any]) -> None:
    controller = event["controller"]
    vehicule = event["vehicule"]
    previous_location = event["previous_location"]
    controller._handleTheftDetectionNoLock(vehicule, previous_location)


def handle_audit(event: Dict[str, Any]) -> None:
    controller = event["controller"]
    vehicule = event["vehicule"]
    if controller.auditLogger:
        controller.auditLogger.logEvent(f"TELEMETRY_PROCESSED: Vehicle {vehicule.vehiculeId}")
