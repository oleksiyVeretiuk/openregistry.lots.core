# -*- coding: utf-8 -*-
import unittest

from openregistry.lots.core.tests import lots


def suite():
    tests = unittest.TestSuite()
    tests.addTest(lots.suite())
    return tests


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
