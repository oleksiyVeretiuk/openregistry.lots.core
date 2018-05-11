# -*- coding: utf-8 -*-
from datetime import datetime

from openprocurement.api.tests.base import (
    create_blacklist,  # noqa forwarded import
    PrefixedRequestClass,  # noqa forwarded import
    DumpsTestAppwebtest,  # noqa forwarded import
    BaseResourceWebTest,
    BaseWebTest,  # noqa forwarded import
    snitch  # noqa forwarded import
)

now = datetime.now()


class DummyException(Exception):
    pass


class BaseLotWebTest(BaseResourceWebTest):

    resource_name = 'lots'
