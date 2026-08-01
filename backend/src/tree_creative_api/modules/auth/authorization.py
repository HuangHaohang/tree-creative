from tree_creative_api.modules.auth.domain import Principal


class AuthorizationService:
    @staticmethod
    def allows(principal: Principal | None, permission: str) -> bool:
        return principal is not None and permission in principal.permissions
