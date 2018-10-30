# -*- coding: utf-8 -*-

from openprocurement.api.interfaces import (  # noqa forwarded import
    IContentConfigurator,
    IResourceManager,
)
from zope.interface import (
    Attribute
)


class ILotManager(IResourceManager):
    name = Attribute('Asset name')

    def create_lot(request):
        raise NotImplementedError
