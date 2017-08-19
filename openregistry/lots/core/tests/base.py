# -*- coding: utf-8 -*-
import json
import os
from uuid import uuid4
from copy import deepcopy
from urllib import urlencode
from base64 import b64encode
from datetime import datetime
from requests.models import Response
from webtest import TestApp

from openregistry.api.tests.base import BaseWebTest, BaseResourceWebTest
from openregistry.api.utils import apply_data_patch
from openregistry.api.constants import SESSION


now = datetime.now()


class BaseLotWebTest(BaseResourceWebTest):

    resource_name = 'lots'
    initial_data = None
    initial_status = None
    docservice = False
