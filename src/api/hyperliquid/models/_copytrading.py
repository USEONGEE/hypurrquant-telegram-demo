from typing import TypedDict, List

SubscribersCountResponse = TypedDict(
    "SubscribersCountResponse",
    {
        "count": int,
        "max": int,
    },
)


class SubscriberDict(TypedDict):
    subscriber_id: str
    created_at: str  # ISO 8601 formatted datetime string


class SubscriptionItemDict(TypedDict):
    target_id: str
    subscribers: List[SubscriberDict]


class ListSubscriptionsResponse(TypedDict):
    total: int
    page: int
    page_size: int
    items: List[SubscriptionItemDict]
