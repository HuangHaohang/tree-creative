from dataclasses import dataclass, field
from datetime import datetime


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


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    id: str
    display_name: str
    avatar_url: str | None
    organization_name: str | None
    title: str | None
    employee_id: str | None
    status: str
    permissions: frozenset[str]
    wps_user_id: str
    wps_company_id: str


@dataclass(frozen=True, slots=True)
class LoginTransaction:
    redirect_uri: str
    return_path: str
    created_at: datetime
