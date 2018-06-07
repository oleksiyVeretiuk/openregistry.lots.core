# -*- coding: utf-8 -*-
from logging import getLogger

LOGGER = getLogger(__name__)


def includeme(config, plugin_map):  # pylint: disable=unused-argument
    config.scan("openregistry.lots.core.plugins.transferring.views")
    LOGGER.info("Included lots transferring plugin",
                extra={'MESSAGE_ID': 'included_plugin'})
