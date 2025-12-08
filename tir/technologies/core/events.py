from typing import Callable, Dict, List, Any

"""
    Event bus for temporary decoupling during WebApp → POUI migration.

    This module will be deprecated once all WebApp screens are migrated to POUI.
    TODO: Remove after migration is complete

    Design Patterns:
    - **Observer**: Loose coupling via publish-subscribe for temporary migration needs
    """

_subscribers: Dict[str, List[Callable[..., Any]]] = {}

def subscribe(event_name: str, handler: Callable[..., Any]) -> None:
    """Registra um handler para um evento específico."""
    _subscribers.setdefault(event_name, []).append(handler)


def emit(event_name: str, *args, **kwargs) -> None:
    """Emite um evento, chamando todos os handlers registrados."""
    for handler in _subscribers.get(event_name, []):
        handler(*args, **kwargs)
