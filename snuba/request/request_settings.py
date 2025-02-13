from abc import ABC, abstractmethod
from typing import List, Optional, Sequence

from snuba.state.quota import ResourceQuota
from snuba.state.rate_limit import RateLimitParameters


class RequestSettings(ABC):
    """
    Settings that apply to how the query in the request should be run.

    The settings provided in this class do not directly affect the SQL statement that will be created
    (i.e. they do not directly appear in the SQL statement).

    They can indirectly affect the SQL statement that will be formed. For example, `turbo` affects
    the formation of the query for projects, but it doesn't appear in the SQL statement.
    """

    def __init__(self, referrer: str) -> None:
        self.referrer = referrer

    @abstractmethod
    def get_turbo(self) -> bool:
        pass

    @abstractmethod
    def get_consistent(self) -> bool:
        pass

    @abstractmethod
    def get_debug(self) -> bool:
        pass

    @abstractmethod
    def get_parent_api(self) -> str:
        pass

    @abstractmethod
    def get_dry_run(self) -> bool:
        pass

    @abstractmethod
    def get_legacy(self) -> bool:
        pass

    @abstractmethod
    def get_team(self) -> str:
        pass

    @abstractmethod
    def get_feature(self) -> str:
        pass

    @abstractmethod
    def get_app_id(self) -> str:
        pass

    @abstractmethod
    def get_rate_limit_params(self) -> Sequence[RateLimitParameters]:
        pass

    @abstractmethod
    def add_rate_limit(self, rate_limit_param: RateLimitParameters) -> None:
        pass

    @abstractmethod
    def get_resource_quota(self) -> Optional[ResourceQuota]:
        pass

    @abstractmethod
    def set_resource_quota(self, quota: ResourceQuota) -> None:
        pass


class HTTPRequestSettings(RequestSettings):
    """
    Settings that are applied to all Requests initiated via the HTTP api. Allows
    parameters to be customized, defaults to using global rate limits and allows
    additional rate limits to be added.
    """

    def __init__(
        self,
        referrer: str = "<unknown>",
        turbo: bool = False,
        consistent: bool = False,
        debug: bool = False,
        parent_api: str = "<unknown>",
        dry_run: bool = False,
        legacy: bool = False,
        team: str = "<unknown>",
        feature: str = "<unknown>",
        app_id: str = "default",
    ) -> None:
        super().__init__(referrer=referrer)
        self.__turbo = turbo
        self.__consistent = consistent
        self.__debug = debug
        self.__parent_api = parent_api
        self.__dry_run = dry_run
        self.__legacy = legacy
        self.__team = team
        self.__feature = feature
        self.__app_id = app_id
        self.__rate_limit_params: List[RateLimitParameters] = []
        self.__resource_quota: Optional[ResourceQuota] = None

    def get_turbo(self) -> bool:
        return self.__turbo

    def get_consistent(self) -> bool:
        return self.__consistent

    def get_debug(self) -> bool:
        return self.__debug

    def get_parent_api(self) -> str:
        return self.__parent_api

    def get_dry_run(self) -> bool:
        return self.__dry_run

    def get_legacy(self) -> bool:
        return self.__legacy

    def get_team(self) -> str:
        return self.__team

    def get_app_id(self) -> str:
        return self.__app_id

    def get_feature(self) -> str:
        return self.__feature

    def get_rate_limit_params(self) -> Sequence[RateLimitParameters]:
        return self.__rate_limit_params

    def add_rate_limit(self, rate_limit_param: RateLimitParameters) -> None:
        self.__rate_limit_params.append(rate_limit_param)

    def get_resource_quota(self) -> Optional[ResourceQuota]:
        return self.__resource_quota

    def set_resource_quota(self, quota: ResourceQuota) -> None:
        self.__resource_quota = quota


class SubscriptionRequestSettings(RequestSettings):
    """
    Settings that are applied to Requests initiated via Subscriptions. Hard code most
    parameters and skips all rate limiting.
    """

    def __init__(
        self,
        referrer: str,
        consistent: bool = True,
        parent_api: str = "subscription",
        team: str = "workflow",
        feature: str = "subscription",
        app_id: str = "default",
    ) -> None:
        super().__init__(referrer=referrer)
        self.__consistent = consistent
        self.__parent_api = parent_api
        self.__team = team
        self.__feature = feature
        self.__app_id = app_id

    def get_turbo(self) -> bool:
        return False

    def get_consistent(self) -> bool:
        return self.__consistent

    def get_debug(self) -> bool:
        return False

    def get_parent_api(self) -> str:
        return self.__parent_api

    def get_dry_run(self) -> bool:
        return False

    def get_legacy(self) -> bool:
        return False

    def get_team(self) -> str:
        return self.__team

    def get_app_id(self) -> str:
        return self.__app_id

    def get_feature(self) -> str:
        return self.__feature

    def get_rate_limit_params(self) -> Sequence[RateLimitParameters]:
        return []

    def add_rate_limit(self, rate_limit_param: RateLimitParameters) -> None:
        pass

    def get_resource_quota(self) -> Optional[ResourceQuota]:
        return None

    def set_resource_quota(self, quota: ResourceQuota) -> None:
        pass
