# -*- coding: utf-8 -*-
from openprocurement.api.constants import (  # noqa: F401
    TZ, # noqa forwarded import
    DOCUMENT_TYPES, # noqa forwarded import
    ROUTE_PREFIX, # noqa forwarded import
    IDENTIFIER_CODES, # noqa forwarded import
    SANDBOX_MODE, # noqa forwarded import
    LOKI_DOCUMENT_TYPES, # noqa forwarded import
    DEFAULT_CURRENCY, # noqa forwarded import
)


DEFAULT_LOT_TYPE = 'basic'

LOT_STATUSES = ["draft", "pending", "deleted", "pending.deleted", "verification", "recomposed",
                "active.salable", "pending.dissolution", "dissolved", "active.awaiting",
                "active.auction", "pending.sold", "sold"]
