# -*- coding: utf-8 -*-
from openprocurement.api.adapters import ContentConfigurator


class LotConfigurator(ContentConfigurator):
    """ Lot configuration adapter """

    name = "Lot Configurator"
    model = None
