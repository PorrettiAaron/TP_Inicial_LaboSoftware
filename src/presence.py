# presence.py
from dataclasses import dataclass
from typing import Dict, Callable, Optional
from time import time

@dataclass
class Track:
    last_seen: float = 0.0
    seen_count: int = 0
    is_present: bool = False
    last_toggle: float = 0.0

class PresenceManager:
    def __init__(
        self,
        on_event: Callable[[str, int, float], None],
        disappear_seconds: float = 10.0,
        cooldown_seconds: float = 30.0,
        now_provider: Callable[[], float] = time,
    ) -> None:
        self.on_event = on_event
        self.disappear_seconds = disappear_seconds
        self.cooldown_seconds = cooldown_seconds
        self.now = now_provider
        self._tracks: Dict[int, Track] = {}

    def detection(self, legajo: int, t: Optional[float] = None) -> None:
        if t is None:
            t = self.now()
        tr = self._tracks.get(legajo)
        if tr is None:
            tr = Track()
            self._tracks[legajo] = tr
        if not tr.is_present:
            if t - tr.last_toggle >= self.cooldown_seconds:
                tr.last_seen = t
                tr.seen_count+=1
                tr.is_present = True
                tr.last_toggle = t
                self.on_event("entrada", legajo, t)
        else:
            if t - tr.last_seen >= self.disappear_seconds and t - tr.last_toggle >= self.cooldown_seconds:
                tr.is_present = False
                tr.last_toggle = t
                self.on_event("salida", legajo, t)
        print(tr)

    def clear(self):
        self._tracks.clear()

    def get_state(self, legajo: int) -> Optional[Track]:
        return self._tracks.get(legajo)