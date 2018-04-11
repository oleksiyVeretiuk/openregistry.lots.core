# -*- coding: utf-8 -*-

from openprocurement.api.constants import (
    TZ,
    DOCUMENT_TYPES,
    ROUTE_PREFIX
)


DEFAULT_LOT_TYPE = 'basic'

LOT_STATUSES = ["draft", "pending", "deleted", "verification", "recomposed",
                "active.salable", "pending.dissolution", "dissolved", "active.awaiting",
                "active.auction", "pending.sold", "sold"]
