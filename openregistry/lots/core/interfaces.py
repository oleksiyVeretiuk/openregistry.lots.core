# -*- coding: utf-8 -*-

from openprocurement.api.interfaces import IContentConfigurator  # noqa forwarded import
from zope.interface import (
    Attribute, Interface
)


class ILotManager(Interface):
    name = Attribute('Asset name')

    def create_lot(request):
        raise NotImplementedError
