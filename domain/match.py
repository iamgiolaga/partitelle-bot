"""The match as the bot reasons about it, free of storage and Telegram concerns."""

from dataclasses import dataclass, field
from datetime import datetime

from domain.schedule import next_start
from utils.constants import default_message, default_target

# the pitch the /bamboo command starts every match with
BAMBOO_PITCH = (
    "Crespi Sport Village \n"
    "\n"
    "Via Carlo Valvassori Peroni, 48, 20133 \n"
    "Milano, MI, 02 266 3774 \n"
    "https://g.co/kgs/L9b6KZ"
)


@dataclass(frozen=True)
class Participant:
    name: str
    is_maybe: bool = False


@dataclass(frozen=True)
class Teams:
    black: tuple[str, ...]
    white: tuple[str, ...]

    @property
    def members(self) -> tuple[str, ...]:
        return self.black + self.white

    def contains(self, name: str) -> bool:
        return name in self.members

    def as_dict(self) -> dict[str, list[str]]:
        return {"black": list(self.black), "white": list(self.white)}


@dataclass
class Match:
    chat_id: int
    participants: list[Participant] = field(default_factory=list)
    starts: datetime = field(default_factory=next_start)
    target: int = default_target
    description: str | None = default_message
    pitch: str | None = None
    summary_message_id: int | None = None
    teams: Teams | None = None

    @classmethod
    def new(cls, chat_id: int | str, pitch: str | None = None) -> "Match":
        return cls(chat_id=int(chat_id), starts=next_start(), pitch=pitch)

    def find(self, name: str, is_maybe: bool) -> Participant | None:
        for participant in self.participants:
            if participant.name == name and participant.is_maybe == is_maybe:
                return participant
        return None

    def confirmed_names(self) -> list[str]:
        return [p.name for p in self.participants if not p.is_maybe]

    @property
    def confirmed_count(self) -> int:
        return len(self.confirmed_names())

    @property
    def maybe_count(self) -> int:
        return len(self.participants) - self.confirmed_count

    @property
    def has_room(self) -> bool:
        """Maybe participants hold a place too."""
        return len(self.participants) < self.target
