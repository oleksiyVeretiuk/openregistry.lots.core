# -*- coding: utf-8 -*-
import os
import unittest
from openregistry.lots.core.tests.base import BaseLotWebTest
from openregistry.api.tests.blanks.mixins import CoreResourceTestMixin


class LotResourceTest(BaseLotWebTest, CoreResourceTestMixin):
    relative_to = os.path.dirname(__file__)


def suite():
    tests = unittest.TestSuite()
    tests.addTest(unittest.makeSuite(LotResourceTest))
    return tests


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
