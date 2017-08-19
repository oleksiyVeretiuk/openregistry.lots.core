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


class DumpsTestAppwebtest(TestApp):
    hostname = "api-sandbox.openregistry.org"

    def do_request(self, req, status=None, expect_errors=None):
        req.headers.environ["HTTP_HOST"] = self.hostname
        if hasattr(self, 'file_obj') and not self.file_obj.closed:
            self.file_obj.write(req.as_bytes(True))
            self.file_obj.write("\n")
            if req.body:
                try:
                    self.file_obj.write(
                            'DATA:\n' + json.dumps(json.loads(req.body), indent=2, ensure_ascii=False).encode('utf8'))
                    self.file_obj.write("\n")
                except:
                    pass
            self.file_obj.write("\n")
        resp = super(DumpsTestAppwebtest, self).do_request(req, status=status, expect_errors=expect_errors)
        if hasattr(self, 'file_obj') and not self.file_obj.closed:
            headers = [(n.title(), v)
                       for n, v in resp.headerlist
                       if n.lower() != 'content-length']
            headers.sort()
            self.file_obj.write(str('Response: %s\n%s\n') % (
                resp.status,
                str('\n').join([str('%s: %s') % (n, v) for n, v in headers]),
            ))

            if resp.testbody:
                try:
                    self.file_obj.write(json.dumps(json.loads(resp.testbody), indent=2, ensure_ascii=False).encode('utf8'))
                except:
                    pass
            self.file_obj.write("\n\n")
        return resp
