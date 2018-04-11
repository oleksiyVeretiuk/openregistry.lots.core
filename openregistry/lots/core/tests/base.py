# -*- coding: utf-8 -*-
from datetime import datetime

from openprocurement.api.tests.base import (
    create_blacklist,
    PrefixedRequestClass,
    DumpsTestAppwebtest,
    BaseResourceWebTest,
    BaseWebTest,
    snitch
)

now = datetime.now()


class BaseLotWebTest(BaseResourceWebTest):

    resource_name = 'lots'
