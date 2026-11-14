from typing import Protocol
from booking.domain.events import DomainEvent

class EventBus(Protocol):
    async def publish(self, event: DomainEvent) -> None: ...
