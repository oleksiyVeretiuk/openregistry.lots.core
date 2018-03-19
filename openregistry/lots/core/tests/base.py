# -*- coding: utf-8 -*-
from datetime import datetime

from openprocurement.api.tests.base import BaseResourceWebTest


now = datetime.now()


class BaseLotWebTest(BaseResourceWebTest):

    resource_name = 'lots'
