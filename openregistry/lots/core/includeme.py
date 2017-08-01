from pkg_resources import iter_entry_points
from pyramid.interfaces import IRequest
from openregistry.lots.core.utils import (
    extract_lot, isLot, register_lotType,
    lot_from_data, SubscribersPicker
)
from openregistry.api.interfaces import IContentConfigurator
from openregistry.lots.core.models import ILot
from openregistry.lots.core.adapters import LotConfigurator


def includeme(config):
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
    settings = config.get_settings()
    plugins = settings.get('plugins') and settings['plugins'].split(',')
    for entry_point in iter_entry_points('openregistry.lots.core.plugins'):
        if not plugins or entry_point.name in plugins:
            plugin = entry_point.load()
            plugin(config)
