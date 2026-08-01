from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ExternalIdentity:
    provider: str
    subject: str
    claims: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Principal:
    user_id: str
    display_name: str
    permissions: frozenset[str] = field(default_factory=frozenset)
    external_identity: ExternalIdentity | None = None
