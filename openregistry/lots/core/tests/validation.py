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


class TestValidatePostLotRole(unittest.TestCase):

    def setUp(self):
        self.mocked_request = mock.MagicMock()
        self.mocked_request.errors = mock.MagicMock()
        self.mocked_request.errors.add = mock.MagicMock()

        self.mocked_handler = mock.MagicMock()
        self.mocked_handler.side_effect = [DummyException, DummyException]

    def test_concierge_post(self):
        self.mocked_request.authenticated_role = 'concierge'
        with self.assertRaises(DummyException):
            validate_post_lot_role(self.mocked_request, self.mocked_handler)

        self.mocked_handler.assert_called_with(self.mocked_request)
        self.mocked_request.errors.add.assert_called_with('body', 'accreditation', 'Can\'t create lot as bot')
        assert self.mocked_request.errors.status == 403
        self.mocked_request.errors.status = None

    def test_convoy_post(self):
        self.mocked_request.authenticated_role = 'convoy'
        with self.assertRaises(DummyException):
            validate_post_lot_role(self.mocked_request, self.mocked_handler)

            self.mocked_handler.assert_called_with(self.mocked_request)
        self.mocked_request.errors.add.assert_called_with('body', 'accreditation', 'Can\'t create lot as bot')
        assert self.mocked_request.errors.status == 403


class TestValidateLotDocumentUpdateNotByAuthorOrLotOwner(unittest.TestCase):

    def setUp(self):
        self.mocked_request = mock.MagicMock()
        self.mocked_request.errors = mock.MagicMock()
        self.mocked_request.errors.add = mock.MagicMock()
        self.mocked_request.errors.status = None
        self.mocked_request.authenticated_role = mock.MagicMock()

        self.mocked_request.context = mock.MagicMock()

        self.mocked_handler = mock.MagicMock()
        self.mocked_handler.side_effect = [DummyException]

    def test_changing_by_not_owner_not_author(self):
        self.mocked_request.authenticated_role = 'not_lot_owner'
        self.mocked_request.context = mock.MagicMock(author=None)
        with self.assertRaises(DummyException):
            validate_lot_document_update_not_by_author_or_lot_owner(self.mocked_request, self.mocked_handler)
        self.mocked_handler.assert_called_with(self.mocked_request)
        self.mocked_request.errors.add.assert_called_with('url', 'role', 'Can update document only author')
        assert self.mocked_request.errors.status == 403

    def test_changing_by_owner_not_author(self):
        self.mocked_request.authenticated_role = 'lot_owner'
        self.mocked_request.context = mock.MagicMock(author='author')
        with self.assertRaises(DummyException):
            validate_lot_document_update_not_by_author_or_lot_owner(self.mocked_request, self.mocked_handler)

        self.mocked_handler.assert_called_with(self.mocked_request)
        self.mocked_request.errors.add.assert_called_with('url', 'role', 'Can update document only author')
        assert self.mocked_request.errors.status == 403

    def test_success_changing_by_owner(self):
        self.mocked_request.authenticated_role = 'lot_owner'
        self.mocked_request.context = mock.MagicMock(author=None)
        validate_lot_document_update_not_by_author_or_lot_owner(self.mocked_request, self.mocked_handler)
        assert self.mocked_request.errors.status is None

    def test_success_changing_by_owner_and_authot(self):
        self.mocked_request.authenticated_role = 'author'
        self.mocked_request.context = mock.MagicMock(author='author')
        validate_lot_document_update_not_by_author_or_lot_owner(self.mocked_request, self.mocked_handler)
        assert self.mocked_request.errors.status is None


@mock.patch('openregistry.lots.core.validation.raise_operation_error')
class TestValidateUpdateItemInNotAllowedStatus(unittest.TestCase):

    def setUp(self):
        self.mocked_request = mock.MagicMock()
        self.mocked_request.errors = mock.MagicMock()
        self.mocked_request.errors.add = mock.MagicMock()

        self.mocked_request.authenticated_role = mock.MagicMock()

        self.mocked_request.validated = {'lot_status': 'status'}

        self.mocked_request.content_configurator = mock.MagicMock(item_editing_allowed_statuses=['status'])

        self.mocked_handler = mock.MagicMock()

    def test_when_lot_status_in_constant(self, mocked_raiser):
        validate_update_item_in_not_allowed_status(self.mocked_request, self.mocked_handler)
        assert mocked_raiser.call_count == 0

    def test_when_lot_status_not_in_constant(self, mocked_raiser):
        self.mocked_request.validated['lot_status'] = 'wrong_status'
        validate_update_item_in_not_allowed_status(self.mocked_request, self.mocked_handler)
        assert mocked_raiser.call_count == 1
        mocked_raiser.assert_called_with(
            self.mocked_request,
            self.mocked_handler,
            'Can\'t update item in current ({}) lot status'.format(self.mocked_request.validated['lot_status']))


@mock.patch('openregistry.lots.core.validation.validate_t_accreditation')
@mock.patch('openregistry.lots.core.validation.validate_accreditations')
@mock.patch('openregistry.lots.core.validation.update_logging_context')
@mock.patch('openregistry.lots.core.validation.validate_json_data')
@mock.patch('openregistry.lots.core.validation.validate_data')
class TestValidateLotData(unittest.TestCase):

    def setUp(self):
        # Mock request
        self.request = mock.MagicMock()
        self.request.lot_from_data = mock.MagicMock()
        self.request.check_accreditation = mock.MagicMock()
        self.request.errors = mock.MagicMock(add=mock.MagicMock(), status=None)

        # Mock model that returned by request.lot_from_data
        self.model = mock.MagicMock(create_accreditation='AB')
        self.data = {'status': 'pending'}

    def test_success_validation(
            self,
            validated_data,
            validated_json,
            update_context,
            validate_accreditations,
            validate_t_accreditation,
        ):
        validated_json.side_effect = [self.data]
        self.request.lot_from_data.side_effect = [self.model]

        validate_lot_data(self.request)

        update_context.assert_called_with(self.request, {'lot_id': '__new__'})
        validated_json.assert_called_with(self.request)
        self.request.lot_from_data.assert_called_with({'status': 'pending'}, create=False)
        assert validate_accreditations.call_count == 1
        assert validate_t_accreditation.call_count == 1


@mock.patch('openregistry.lots.core.validation.validate_change_status')
@mock.patch('openregistry.lots.core.validation.validate_data')
@mock.patch('openregistry.lots.core.validation.validate_json_data')
@mock.patch('openregistry.lots.core.validation.raise_operation_error')
class TestValidatePatchLotData(unittest.TestCase):

    def setUp(self):
        # Mock request
        self.mocked_request = mock.MagicMock(authenticated_role='role')
        self.mocked_request.lot = Lot()
        self.mocked_request.validated = {'resource_type': 'lot'}
        self.mocked_request.lot.fields = {'context_status': None}
        self.mocked_request.context = mock.MagicMock(status='context_status')
        self.mocked_request.content_configurator = mock.MagicMock()
        self.mocked_request.check_accreditation = mock.MagicMock()

        # Mock error handler
        self.mocked_handler = mock.MagicMock()

    def test_success_validation(self, mocked_raise, mocked_validate_json, mocked_validate_data, mocked_change_status):
        mocked_raise.side_effect = [DummyException]
        data = {'status': 'new_status'}
        self.mocked_request.content_configurator.available_statuses = {
            'context_status': {
                'editing_permissions': ['role']
            }
        }
        mocked_validate_json.side_effect = [data]

        validate_patch_lot_data(self.mocked_request, self.mocked_handler)

        assert mocked_validate_json.call_count == 1
        mocked_validate_json.assert_called_with(self.mocked_request)

        assert mocked_change_status.call_count == 1
        mocked_change_status.assert_called_with(
            self.mocked_request,
            self.mocked_handler,
            )

        assert mocked_validate_data.call_count == 1
        mocked_validate_data.assert_called_with(self.mocked_request, Lot,
                                                data=data)

        assert mocked_raise.call_count == 0

    def test_wrong_authenticated_role(self, mocked_raise, mocked_validate_json, mocked_validate_data, mocked_change_status):
        data = {'status': 'new_status'}
        mocked_raise.side_effect = [DummyException]
        self.mocked_request.content_configurator.available_statuses = {
            'context_status': {
                'editing_permissions': ['new_role']
            }
        }
        mocked_validate_json.side_effect = [data]

        with self.assertRaises(DummyException):
            validate_patch_lot_data(self.mocked_request, self.mocked_handler)

        assert mocked_validate_json.call_count == 1
        mocked_validate_json.assert_called_with(self.mocked_request)

        assert mocked_validate_data.call_count == 0

        assert mocked_change_status.call_count == 0

        assert mocked_raise.call_count == 1
        msg = 'Can\'t update {} in current ({}) status'.format(
                self.mocked_request.validated['resource_type'],
                self.mocked_request.context.status
            )
        mocked_raise.assert_called_with(
            self.mocked_request,
            self.mocked_handler,
            msg
        )

    def test_patch_to_default(self, mocked_raise, mocked_validate_json, mocked_validate_data, mocked_change_status):
        data = {'status': 'draft'}
        mocked_raise.side_effect = [DummyException]
        self.mocked_request.content_configurator.available_statuses = {
            'context_status': {
                'editing_permissions': ['role']
            }
        }
        mocked_validate_json.side_effect = [data]

        with self.assertRaises(DummyException):
            validate_patch_lot_data(self.mocked_request, self.mocked_handler)

        assert mocked_validate_json.call_count == 1
        mocked_validate_json.assert_called_with(self.mocked_request)

        assert mocked_validate_data.call_count == 0

        assert mocked_change_status.call_count == 0

        assert mocked_raise.call_count == 1

        mocked_raise.assert_called_with(
            self.mocked_request,
            self.mocked_handler,
            'Can\'t switch lot to {} status'.format(data['status'])
        )


def suite():
    tests = unittest.TestSuite()
    tests.addTest(unittest.makeSuite(TestValidateLotData))
    tests.addTest(unittest.makeSuite(TestValidateLotDocumentUpdateNotByAuthorOrLotOwner))
    tests.addTest(unittest.makeSuite(TestValidatePatchLotData))
    tests.addTest(unittest.makeSuite(TestValidatePostLotRole))
    tests.addTest(unittest.makeSuite(TestValidateUpdateItemInNotAllowedStatus))
    return tests


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
