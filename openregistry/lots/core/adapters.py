# -*- coding: utf-8 -*-
from openprocurement.api.adapters import ContentConfigurator
from openprocurement.api.utils import error_handler
from openprocurement.api.managers import (  # noqa: F401
    Manager,  # noqa forwarded import
)


class LotConfigurator(ContentConfigurator):
    """ Lot configuration adapter """

    name = "Lot Configurator"
    model = None


class LotManagerAdapter(object):
    name = 'Lot Manager'
    context = None

    def __init__(self, context):
        self.context = context

    def _validate(self, request, validators):
        kwargs = {'request': request, 'error_handler': error_handler}
        for validator in validators:
            validator(**kwargs)

    def create_lot(self, request):
        pass
