# -*- coding: utf-8 -*-
import unittest

from openregistry.assets.core.tests import asset, migration

def suite():
    suite = unittest.TestSuite()
    suite.addTest(asset.suite())
    suite.addTest(migration.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
