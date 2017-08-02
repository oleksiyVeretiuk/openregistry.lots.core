# -*- coding: utf-8 -*-
import unittest

from openregistry.lots.core.tests import lot


def suite():
    suite = unittest.TestSuite()
    suite.addTest(lot.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
