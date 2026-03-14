from typing import Callable, Dict, List, Any


class EventBus:
    """Simple in-process event bus for publishing domain events."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}

    def subscribe(self, event_name: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Register a handler for a given event name."""
        self._subscribers.setdefault(event_name, []).append(handler)

    def publish(self, event_name: str, event: Dict[str, Any]) -> None:
        """Publish an event to all subscribers in registration order."""
        for handler in self._subscribers.get(event_name, []):
            handler(event)
            if event.get("stop_processing"):
                break
