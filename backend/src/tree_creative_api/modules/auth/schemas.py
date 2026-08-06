from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class DepartmentReference(CamelModel):
    id: str
    name: str
    path: str | None = None
    is_primary: bool = False


class ContactDetails(CamelModel):
    email: str | None = None
    phone: str | None = None
    telephone: str | None = None


class GatewayExternalIdentity(CamelModel):
    provider: str
    external_user_id: str
    external_tenant_id: str | None = None


class GatewayUser(CamelModel):
    id: str
    display_name: str
    avatar: str | None = None
    status: str = "unknown"
    title: str | None = None
    employee_id: str | None = None
    source_role: str | None = None
    primary_department: DepartmentReference | None = None
    departments: list[DepartmentReference] = Field(default_factory=list)
    contacts: ContactDetails = Field(default_factory=ContactDetails)
    contact_visibility: str = "masked"
    external_identities: list[GatewayExternalIdentity] = Field(default_factory=list)


class GatewayDepartmentNode(CamelModel):
    id: str
    name: str
    parent_id: str | None = None
    path: str | None = None
    enabled: bool = True
    children: list["GatewayDepartmentNode"] = Field(default_factory=list)
    users: list[GatewayUser] = Field(default_factory=list)


class GatewayTreeUserStats(CamelModel):
    total: int
    attached: int
    unassigned: list[GatewayUser] = Field(default_factory=list)


class GatewayDepartmentTree(CamelModel):
    tree: GatewayDepartmentNode
    users: GatewayTreeUserStats


class GatewayMember(CamelModel):
    id: str
    name: str
    avatar: str | None = None
    account_status: str | None = None
    employment_status: str | None = None
    enabled: bool = True
    departed: bool = False
    primary_department: DepartmentReference | None = None
    departments: list[DepartmentReference] = Field(default_factory=list)


class GatewayMemberPage(CamelModel):
    page_size: int
    next_cursor: str | None = None
    has_more: bool
    total: int | None = None


class GatewayMembersResult(CamelModel):
    items: list[GatewayMember]
    page: GatewayMemberPage


class GatewayTokenVerification(CamelModel):
    active: bool
    reason: str | None = None
    token_type: str | None = None
    access_expires_at: datetime | None = None
    refresh_expires_at: datetime | None = None
    wps_user_id: str | None = None
    wps_company_id: str | None = None


class GatewayTokenRefresh(CamelModel):
    token_envelope: str
    token_type: str
    access_expires_at: datetime
    refresh_expires_at: datetime


class SessionUser(CamelModel):
    id: str
    display_name: str
    avatar_url: str | None = None
    organization_name: str | None = None
    title: str | None = None
    employee_id: str | None = None
    status: str
    permissions: list[str] = Field(default_factory=list)
    wps_user_id: str
    wps_company_id: str


class ServerSession(CamelModel):
    id: str
    csrf_token: str
    token_envelope: str
    access_expires_at: datetime
    refresh_expires_at: datetime
    verified_at: datetime
    created_at: datetime
    user: SessionUser


class CurrentUser(CamelModel):
    id: str
    display_name: str
    avatar_url: str | None = None
    organization_name: str | None = None
    title: str | None = None
    employee_id: str | None = None
    status: str
    permissions: list[str]


class CurrentUserResponse(CamelModel):
    user: CurrentUser
    csrf_token: str


class DirectoryUser(CamelModel):
    id: str
    display_name: str
    avatar_url: str | None = None
    status: str
    title: str | None = None
    employee_id: str | None = None
    primary_department: DepartmentReference | None = None
    departments: list[DepartmentReference] = Field(default_factory=list)
    contacts: ContactDetails = Field(default_factory=ContactDetails)


class DepartmentNode(CamelModel):
    id: str
    name: str
    parent_id: str | None = None
    path: str | None = None
    enabled: bool
    children: list["DepartmentNode"] = Field(default_factory=list)
    users: list[DirectoryUser] = Field(default_factory=list)


class TreeUserStats(CamelModel):
    total: int
    attached: int
    unassigned: list[DirectoryUser] = Field(default_factory=list)


class OrganizationTreeResponse(CamelModel):
    tree: DepartmentNode
    users: TreeUserStats


class DirectoryMember(CamelModel):
    id: str
    display_name: str
    avatar_url: str | None = None
    account_status: str | None = None
    employment_status: str | None = None
    enabled: bool
    departed: bool
    primary_department: DepartmentReference | None = None
    departments: list[DepartmentReference] = Field(default_factory=list)


class MembersPage(CamelModel):
    page_size: int
    next_cursor: str | None = None
    has_more: bool
    total: int | None = None


class OrganizationMembersResponse(CamelModel):
    items: list[DirectoryMember]
    page: MembersPage


class WpsCallbackPayload(CamelModel):
    token_type: str = Field(min_length=1, max_length=64)
    token_envelope: str = Field(min_length=1, max_length=32_768)
    state: str = Field(min_length=1, max_length=512)
    access_expires_at: datetime
    refresh_expires_at: datetime
    wps_user_id: str = Field(min_length=1, max_length=256)
    wps_company_id: str = Field(min_length=1, max_length=256)

    @model_validator(mode="after")
    def validate_expirations(self) -> Self:
        if (
            self.access_expires_at.utcoffset() is None
            or self.refresh_expires_at.utcoffset() is None
        ):
            raise ValueError("WPS callback expiration timestamps must include a timezone")
        if self.access_expires_at > self.refresh_expires_at:
            raise ValueError("WPS callback access expiration cannot exceed refresh expiration")
        return self
