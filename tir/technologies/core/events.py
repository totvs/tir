from typing import Callable, Dict, List, Any

_subscribers: Dict[str, List[Callable[..., Any]]] = {}


def subscribe(event_name: str, handler: Callable[..., Any]) -> None:
    """Registra um handler para um evento específico."""
    _subscribers.setdefault(event_name, []).append(handler)


def emit(event_name: str, *args, **kwargs) -> None:
    """Emite um evento, chamando todos os handlers registrados."""
    for handler in _subscribers.get(event_name, []):
        handler(*args, **kwargs)
