# -*- coding: utf-8 -*-
from openregistry.lots.core.tests.base import snitch
from openprocurement.api.tests.blanks.mixins import (
    ResourceTestMixin,  # noqa forwarded import
    ResourceDocumentTestMixin  # noqa forwarded import
)

from openregistry.lots.core.tests.blanks.extract_credentials import (
    get_extract_credentials,
    forbidden_users
)


class ExtractCredentialsMixin(object):
    """ Mixin with tests for extract_credentials entry point
    """
    valid_user = 'concierge'

    test_get_extract_credentials = snitch(get_extract_credentials)
    test_forbidden_users = snitch(forbidden_users)
