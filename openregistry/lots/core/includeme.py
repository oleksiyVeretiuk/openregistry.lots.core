# -*- coding: utf-8 -*-
from pyramid.interfaces import IRequest
from openregistry.lots.core.utils import (
    extract_lot, isLot, register_lotType,
    lot_from_data, SubscribersPicker
)
from openprocurement.api.interfaces import IContentConfigurator
from openregistry.lots.core.models import ILot
from openregistry.lots.core.adapters import LotConfigurator
from openprocurement.api.utils import configure_plugins


def includeme(config, plugin_config=None):
    from openregistry.lots.core.design import add_design
    add_design()
    config.add_request_method(extract_lot, 'lot', reify=True)

    # lotType plugins support
    config.registry.lotTypes = {}
    config.add_route_predicate('lotType', isLot)
    config.add_subscriber_predicate('lotType', SubscribersPicker)
    config.add_request_method(lot_from_data)
    config.add_directive('add_lotType',
                         register_lotType)
    config.scan("openregistry.lots.core.views")
    config.scan("openregistry.lots.core.subscribers")
    config.registry.registerAdapter(LotConfigurator, (ILot, IRequest),
                                    IContentConfigurator)

    # search for plugins
    if plugin_config and plugin_config.get('plugins'):
        for name in plugin_config['plugins']:
            package_config = plugin_config['plugins'][name]
            configure_plugins(
                config, {name: package_config},
                'openregistry.lots.core.plugins', name
            )
