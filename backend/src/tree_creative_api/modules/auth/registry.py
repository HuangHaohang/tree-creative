from tree_creative_api.modules.auth.ports import IdentityProvider


class DuplicateIdentityProviderError(ValueError):
    pass


class UnknownIdentityProviderError(LookupError):
    pass


class IdentityProviderRegistry:
    def __init__(self, providers: list[IdentityProvider] | None = None) -> None:
        self._providers: dict[str, IdentityProvider] = {}
        for provider in providers or []:
            self.register(provider)

    def register(self, provider: IdentityProvider) -> None:
        if provider.name in self._providers:
            raise DuplicateIdentityProviderError(provider.name)
        self._providers[provider.name] = provider

    def get(self, name: str) -> IdentityProvider:
        try:
            return self._providers[name]
        except KeyError as error:
            raise UnknownIdentityProviderError(name) from error

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))
