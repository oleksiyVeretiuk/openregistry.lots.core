# -*- coding: utf-8 -*-
from datetime import datetime

from openprocurement.api.tests.base import (
    create_blacklist,  # noqa forwarded import
    PrefixedRequestClass,  # noqa forwarded import
    DumpsTestAppwebtest,  # noqa forwarded import
    BaseResourceWebTest,
    BaseWebTest as CoreWebTest,
    snitch  # noqa forwarded import
)

now = datetime.now()


from openprocurement.api.tests.base import MOCK_CONFIG as BASE_MOCK_CONFIG
from openprocurement.api.tests.blanks.related_processes import (
    RelatedProcessesTestMixinBase,  # forwarded import
)
from openprocurement.api.tests.fixtures.mocks import MigrationResourcesDTO_mock  # noqa import fowrard
from openprocurement.api.utils import connection_mock_config
from openregistry.lots.core.tests.fixtures import PARTIAL_MOCK_CONFIG

MOCK_CONFIG = connection_mock_config(PARTIAL_MOCK_CONFIG, ('plugins',), BASE_MOCK_CONFIG)

class DummyException(Exception):
    pass

class BaseWebTest(CoreWebTest):
    mock_config = MOCK_CONFIG


class BaseLotWebTest(BaseResourceWebTest):

    resource_name = 'lots'
    mock_config = MOCK_CONFIG
