# -*- coding: utf-8 -*-
import unittest
import mock

from datetime import timedelta



from openregistry.lots.core.utils import get_now, error_handler
from openregistry.lots.core.models import Lot
from openregistry.lots.core.validation import (
    validate_post_lot_role,
    validate_lot_document_update_not_by_author_or_lot_owner,
    validate_update_item_in_not_allowed_status,
    validate_lot_data,
    validate_patch_lot_data
)
from openregistry.lots.core.tests.base import DummyException


now = get_now()


class DummyValidationTest(unittest.TestCase):

    def test_validate_post_lot_role(self):
        mocked_request = mock.MagicMock()
        mocked_request.errors = mock.MagicMock()
        mocked_request.errors.add = mock.MagicMock()

        mocked_handler = mock.MagicMock()
        mocked_handler.side_effect = [DummyException, DummyException]

        # Check validation failed due to authenticated_role = concierge
        mocked_request.authenticated_role = 'concierge'
        with self.assertRaises(DummyException):
            validate_post_lot_role(mocked_request, mocked_handler)

        mocked_handler.assert_called_with(mocked_request)
        mocked_request.errors.add.assert_called_with('body', 'accreditation', 'Can\'t create lot as bot')
        assert mocked_request.errors.status == 403
        mocked_request.errors.status = None

        # Check validation failed due to authenticated_role = convoy
        mocked_request.authenticated_role = 'convoy'
        with self.assertRaises(DummyException):
            validate_post_lot_role(mocked_request, mocked_handler)

        mocked_handler.assert_called_with(mocked_request)
        mocked_request.errors.add.assert_called_with('body', 'accreditation', 'Can\'t create lot as bot')
        assert mocked_request.errors.status == 403

    def test_validate_lot_document_update_not_by_author_or_lot_owner(self):
        mocked_request = mock.MagicMock()
        mocked_request.errors = mock.MagicMock()
        mocked_request.errors.add = mock.MagicMock()
        mocked_request.authenticated_role = mock.MagicMock()

        mocked_request.context = mock.MagicMock()

        mocked_handler = mock.MagicMock()
        mocked_handler.side_effect = [DummyException, DummyException, DummyException, DummyException]

        # Check validation failed if authenticated_role is not lot_owner and doc.author is None
        mocked_request.authenticated_role = 'not_lot_owner'
        mocked_request.context = mock.MagicMock(author=None)
        with self.assertRaises(DummyException):
            validate_lot_document_update_not_by_author_or_lot_owner(mocked_request, mocked_handler)
        mocked_handler.assert_called_with(mocked_request)
        mocked_request.errors.add.assert_called_with('url', 'role', 'Can update document only author')
        assert mocked_request.errors.status == 403
        mocked_request.status = None

        # Check validation failed if authenticated_role is lot_owner but not equal doc.author
        mocked_request.authenticated_role = 'lot_owner'
        mocked_request.context = mock.MagicMock(author='author')
        with self.assertRaises(DummyException):
            validate_lot_document_update_not_by_author_or_lot_owner(mocked_request, mocked_handler)
        mocked_handler.assert_called_with(mocked_request)
        mocked_request.errors.add.assert_called_with('url', 'role', 'Can update document only author')
        assert mocked_request.errors.status == 403
        mocked_request.errors.status = None

        # Check validation success if authenticated_role is lot_owner and doc.author is none
        mocked_request.authenticated_role = 'lot_owner'
        mocked_request.context = mock.MagicMock(author=None)
        validate_lot_document_update_not_by_author_or_lot_owner(mocked_request, mocked_handler)
        assert mocked_request.errors.status is None

        # Check validation success if authenticated_role is lot_owner and doc.author == lot_owner
        mocked_request.authenticated_role = 'author'
        mocked_request.context = mock.MagicMock(author='author')
        validate_lot_document_update_not_by_author_or_lot_owner(mocked_request, mocked_handler)
        assert mocked_request.errors.status is None

    @mock.patch('openregistry.lots.core.validation.raise_operation_error')
    def test_validate_update_item_in_not_allowed_status(self, mocked_raiser):
        mocked_request = mock.MagicMock()
        mocked_request.errors = mock.MagicMock()
        mocked_request.errors.add = mock.MagicMock()

        mocked_request.authenticated_role = mock.MagicMock()

        mocked_request.validated = {'lot_status': 'status'}

        mocked_request.content_configurator = mock.MagicMock(item_editing_allowed_statuses=['status'])

        mocked_handler = mock.MagicMock()

        # Check validation success if lot_status is in item_editing_allowed_statuses
        validate_update_item_in_not_allowed_status(mocked_request, mocked_handler)
        assert mocked_raiser.call_count == 0

        # Check validation failed if lot_status is not in item_editing_allowed_statuses
        mocked_request.validated['lot_status'] = 'wrong_status'
        validate_update_item_in_not_allowed_status(mocked_request, mocked_handler)
        assert mocked_raiser.call_count == 1
        mocked_raiser.assert_called_with(
            mocked_request,
            mocked_handler,
            'Can\'t update item in current ({}) lot status'.format(mocked_request.validated['lot_status']))

    @mock.patch('openregistry.lots.core.validation.update_logging_context')
    @mock.patch('openregistry.lots.core.validation.validate_json_data')
    @mock.patch('openregistry.lots.core.validation.validate_data')
    def test_validate_lot_data(self, mocked_validated_data, mocked_validated_json, mocked_update_context):

        # Mock request
        mocked_request = mock.MagicMock()
        mocked_request.lot_from_data = mock.MagicMock()
        mocked_request.check_accreditation = mock.MagicMock()
        mocked_request.errors = mock.MagicMock(add=mock.MagicMock(), status=None)

        # Mock error handler
        mocked_handler = mock.MagicMock()

        # Mock model that returned by request.lot_from_data
        mocked_model = mock.MagicMock(create_accreditation='AB')

        data = {'status': 'pending'}

        # Mocking values for check succes validation
        mocked_validated_json.side_effect = [data]
        mocked_validated_data.side_effect = [data]

        mocked_request.lot_from_data.side_effect = [mocked_model]
        mocked_request.check_accreditation.side_effect = [True, False, False]

        validate_lot_data(mocked_request, mocked_handler)
        mocked_update_context.call_count = 1
        mocked_update_context.assert_called_with(mocked_request, {'lot_id': '__new__'})

        mocked_validated_json.call_count = 1
        mocked_validated_json.assert_called_with(mocked_request)

        mocked_validated_data.call_count = 1
        mocked_validated_data.assert_called_with(mocked_request, mocked_model, data=data)

        assert mocked_request.lot_from_data.call_count == 1
        mocked_request.lot_from_data.assert_called_with(data, create=False)

        assert mocked_request.check_accreditation.call_count == 3
        mocked_request.check_accreditation.assert_called_with('t')

        assert mocked_handler.call_count ==  0


        # Mocking values for check failed validation due to broker level
        mocked_handler.side_effect = [DummyException]
        mocked_validated_json.side_effect = [data]

        mocked_request.lot_from_data.side_effect = [mocked_model]
        mocked_request.check_accreditation.side_effect = [False, False]

        with self.assertRaises(DummyException):
            validate_lot_data(mocked_request, mocked_handler)
        mocked_update_context.call_count = 2
        mocked_update_context.assert_called_with(mocked_request, {'lot_id': '__new__'})

        mocked_validated_json.call_count = 2
        mocked_validated_json.assert_called_with(mocked_request)

        mocked_validated_data.call_count = 1

        mocked_request.lot_from_data.call_count = 1
        mocked_request.lot_from_data.assert_called_with({'status': 'pending'}, create=False)

        mocked_request.check_accreditation.call_count = 5
        mocked_request.check_accreditation.assert_called_with('B')

        mocked_handler.assert_called_with(mocked_request.errors)

        mocked_request.errors.add.assert_called_with(
            'body',
            'accreditation',
            'Broker Accreditation level does not permit lot creation'
        )
        assert mocked_request.errors.add.call_count == 1
        assert mocked_request.errors.status == 403

        # Mocking values for check failed validation due to mode/accrediation `t` level
        mocked_request.errors.status = None

        mocked_handler.side_effect = [DummyException]
        mocked_validated_json.side_effect = [data]
        mocked_validated_data.side_effect = [data]

        mocked_request.lot_from_data.side_effect = [mocked_model]
        mocked_request.check_accreditation.side_effect = [True, False, True]

        with self.assertRaises(DummyException):
            validate_lot_data(mocked_request, mocked_handler)
        mocked_update_context.call_count = 3
        mocked_update_context.assert_called_with(mocked_request, {'lot_id': '__new__'})

        mocked_validated_json.call_count = 3
        mocked_validated_json.assert_called_with(mocked_request)

        mocked_validated_data.call_count = 2
        mocked_validated_data.assert_called_with(mocked_request, mocked_model, data=data)

        mocked_request.lot_from_data.call_count = 1
        mocked_request.lot_from_data.assert_called_with({'status': 'pending'}, create=False)

        mocked_request.check_accreditation.call_count = 8
        mocked_request.check_accreditation.assert_called_with('t')

        mocked_handler.assert_called_with(mocked_request)

        mocked_request.errors.add.assert_called_with(
            'body',
            'mode',
            'Broker Accreditation level does not permit lot creation'
        )
        assert mocked_request.errors.add.call_count == 2
        assert mocked_request.errors.status == 403

    @mock.patch('openregistry.lots.core.validation.validate_data')
    @mock.patch('openregistry.lots.core.validation.validate_json_data')
    @mock.patch('openregistry.lots.core.validation.raise_operation_error')
    def test_validate_patch_lot_data(self, mocked_raise, mocked_validate_json, mocked_validate_data):
        # Mock request
        mocked_request = mock.MagicMock(authenticated_role='role')
        mocked_request.lot = Lot()
        mocked_request.validated = {'resource_type': 'lot'}
        mocked_request.lot.fields = {'context_status': None}
        mocked_request.context = mock.MagicMock(status='context_status')
        mocked_request.content_configurator = mock.MagicMock()
        mocked_request.check_accreditation = mock.MagicMock()

        # Mock error handler
        mocked_handler = mock.MagicMock()

        # Mocking values to check success validation
        mocked_raise.side_effect = [DummyException]
        data = {'status': 'new_status'}
        mocked_request.content_configurator.available_statuses = {
            'context_status': {
                'editing_permissions': ['role']
            }
        }
        mocked_validate_json.side_effect = [data]

        validate_patch_lot_data(mocked_request, mocked_handler)

        assert mocked_validate_json.call_count == 1
        mocked_validate_json.assert_called_with(mocked_request)

        assert mocked_validate_data.call_count == 1
        mocked_validate_data.assert_called_with(mocked_request, Lot, True, data)

        assert mocked_raise.call_count == 0


        # Mocking values to check failed validation due to authenticated_role
        data = {'status': 'new_status'}
        mocked_raise.side_effect = [DummyException]
        mocked_request.content_configurator.available_statuses = {
            'context_status': {
                'editing_permissions': ['new_role']
            }
        }
        mocked_validate_json.side_effect = [data]

        with self.assertRaises(DummyException):
            validate_patch_lot_data(mocked_request, mocked_handler)

        assert mocked_raise.call_count == 1
        msg = 'Can\'t update {} in current ({}) status'.format(
                mocked_request.validated['resource_type'],
                mocked_request.context.status
            )
        mocked_raise.assert_called_with(
            mocked_request,
            mocked_handler,
            msg
        )

        # Mocking values to check failed validation due to authenticated_role
        data = {'status': 'draft'}
        mocked_raise.side_effect = [DummyException]
        mocked_request.content_configurator.available_statuses = {
            'context_status': {
                'editing_permissions': ['role']
            }
        }
        mocked_validate_json.side_effect = [data]

        with self.assertRaises(DummyException):
            validate_patch_lot_data(mocked_request, mocked_handler)

        assert mocked_raise.call_count == 2

        mocked_raise.assert_called_with(
            mocked_request,
            mocked_handler,
            'Can\'t switch lot to {} status'.format(data['status'])
        )

def suite():
    tests = unittest.TestSuite()
    tests.addTest(unittest.makeSuite(DummyValidationTest))
    return tests


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
