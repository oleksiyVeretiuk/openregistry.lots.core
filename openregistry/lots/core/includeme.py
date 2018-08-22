# -*- coding: utf-8 -*-
import logging
from pyramid.interfaces import IRequest
from openregistry.lots.core.utils import (
    extract_lot, isLot, register_lotType,
    lot_from_data, SubscribersPicker, get_evenly_plugins
)
from openprocurement.api.interfaces import IContentConfigurator
from openregistry.lots.core.adapters import LotConfigurator
from openregistry.lots.core.models import ILot

from openprocurement.api.utils import get_plugin_aliases

LOGGER = logging.getLogger(__name__)


def includeme(config, plugin_map):
    from openregistry.lots.core.design import add_design
    add_design()
    config.add_request_method(extract_lot, 'lot', reify=True)

    # add accreditation
    config.registry.accreditation['lot'] = {}

    # lotType plugins support
    config.registry.lotTypes = {}
    config.add_route_predicate('_internal_type', isLot)
    config.add_subscriber_predicate('_internal_type', SubscribersPicker)
    config.add_request_method(lot_from_data)
    config.add_directive('add_lotType',
                         register_lotType)
    config.scan("openregistry.lots.core.views")
    config.scan("openregistry.lots.core.subscribers")
    config.registry.registerAdapter(LotConfigurator, (ILot, IRequest),
                                    IContentConfigurator)

    config.registry.lot_type_configurator = {}

    LOGGER.info("Included openprocurement.lots.core plugin", extra={'MESSAGE_ID': 'included_plugin'})

    # Aliases information
    LOGGER.info('Start aliases')
    get_plugin_aliases(plugin_map.get('plugins', {}))
    LOGGER.info('End aliases')

    # search for plugins
    get_evenly_plugins(config, plugin_map['plugins'], 'openregistry.lots.core.plugins')
