# -*- coding: utf-8 -*-
import logging
from openprocurement.api.migration import (  # noqa: forwarded  import
    BaseMigrationsRunner,
    BaseMigrationStep,
)
LOGGER = logging.getLogger(__name__)


def migrate_data(registry, destination=None):
    pass
