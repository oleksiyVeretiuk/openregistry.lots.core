# -*- coding: utf-8 -*-
import unittest
import mock

from couchdb.http import ResourceConflict
from datetime import datetime, timedelta
from schematics.exceptions import ModelValidationError

from openregistry.lots.core.utils import (
    get_now,
    generate_lot_id,
    extract_lot,
    extract_lot_adapter,
    lot_from_data,
    register_lotType,
    apply_patch,
    lot_serialize,
    save_lot,
    SubscribersPicker,
    isLot,
    store_lot,
    get_lot_types
)
from openregistry.lots.core.models import Lot
from openregistry.lots.core.tests.base import DummyException, BaseLotWebTest

now = get_now()


class TestGenerateLotID(unittest.TestCase):

    def setUp(self):
        self.ctime = datetime.now()
        self.mocked_key = self.ctime.date().isoformat()
        self.server_id = '1'
        self.db = mock.MagicMock()
        self.db.get = mock.MagicMock()
        self.db.save = mock.MagicMock()

    def test_generation_with_server_id(self):
        index = 1
        self.db.get.side_effect = iter([{}])
        mocked_lotIDdoc = 'lotID_' + self.server_id
        mocked_lotID = {self.mocked_key: 2}
        lot_id = 'UA-LR-DGF-{:04}-{:02}-{:02}-{:06}{}'.format(
                                                self.ctime.year,
                                                self.ctime.month,
                                                self.ctime.day,
                                                index,
                                                '-' + self.server_id
                                            )

        returned_lot_id = generate_lot_id(self.ctime, self.db, self.server_id)
        assert lot_id == returned_lot_id
        assert self.db.get.call_count == 1
        self.db.get.assert_called_with(mocked_lotIDdoc, {'_id': mocked_lotIDdoc})
        assert self.db.save.call_count == 1
        self.db.save.assert_called_with(mocked_lotID)

    def test_generation_without_server_id(self):
        index = 1
        self.db.get.side_effect = iter([{}])
        mocked_lotIDdoc = 'lotID'
        mocked_lotID = {self.mocked_key: 2}
        lot_id = 'UA-LR-DGF-{:04}-{:02}-{:02}-{:06}{}'.format(
                                                self.ctime.year,
                                                self.ctime.month,
                                                self.ctime.day,
                                                index,
                                                ''
                                            )

        returned_lot_id = generate_lot_id(self.ctime, self.db)
        assert lot_id == returned_lot_id
        assert self.db.get.call_count == 1
        self.db.get.assert_called_with(mocked_lotIDdoc, {'_id': mocked_lotIDdoc})
        assert self.db.save.call_count == 1
        self.db.save.assert_called_with(mocked_lotID)

    def test_generation_with_index(self):
        index = 2
        self.db.get.side_effect = iter([{self.mocked_key: index}])
        mocked_lotIDdoc = 'lotID'
        mocked_lotID = {self.mocked_key: index + 1}
        lot_id = 'UA-LR-DGF-{:04}-{:02}-{:02}-{:06}{}'.format(
                                                self.ctime.year,
                                                self.ctime.month,
                                                self.ctime.day,
                                                index,
                                                ''
                                            )

        returned_lot_id = generate_lot_id(self.ctime, self.db)
        assert lot_id == returned_lot_id
        assert self.db.get.call_count == 1
        self.db.get.assert_called_with(mocked_lotIDdoc, {'_id': mocked_lotIDdoc})
        assert self.db.save.call_count == 1
        self.db.save.assert_called_with(mocked_lotID)

    def test_while_loop(self):
        self.db.get.side_effect = iter([{}, {}, {}])
        self.db.save.side_effect = iter([DummyException, ResourceConflict, None])
        generate_lot_id(self.ctime, self.db)
        assert self.db.get.call_count == 3
        assert self.db.save.call_count == 3


@mock.patch('openregistry.lots.core.utils.decode_path_info', autospec=True)
@mock.patch('openregistry.lots.core.utils.extract_lot_adapter', autospec=True)
class TestExtractLot(unittest.TestCase):

    def setUp(self):
        self.mocked_request = mock.MagicMock()
        self.mocked_request.environ = {}

    def test_with_key_error(self, mocked_extract_lot_adapter, mocked_decode_path_info):
        mocked_extract_lot_adapter.side_effect = iter(['adapter'])
        returned_value = extract_lot(self.mocked_request)
        assert returned_value is None
        assert mocked_extract_lot_adapter.call_count == 0
        assert mocked_decode_path_info.call_count == 0

    def test_with_path_and_id(self, mocked_extract_lot_adapter, mocked_decode_path_info):
        path = 'domain/api/0/lots/lotID'
        mocked_extract_lot_adapter.side_effect = iter(['adapter'])
        self.mocked_request.environ = {'PATH_INFO': path}
        mocked_decode_path_info.side_effect = iter([path])

        returned_value = extract_lot(self.mocked_request)

        assert returned_value == 'adapter'
        assert mocked_decode_path_info.call_count == 1
        assert mocked_extract_lot_adapter.call_count == 1
        mocked_extract_lot_adapter.assert_called_with(self.mocked_request, path.split('/')[4])

    def test_with_path_len_more_4(self, mocked_extract_lot_adapter, mocked_decode_path_info):
        path = 'domain/api/0/'
        mocked_extract_lot_adapter.side_effect = ['adapter']
        self.mocked_request.environ = {'PATH_INFO': path}
        mocked_decode_path_info.side_effect = iter([path])

        returned_value = extract_lot(self.mocked_request)
        assert returned_value is None
        assert mocked_decode_path_info.call_count == 1
        assert mocked_extract_lot_adapter.call_count == 0

    def test_with_path_without_lots_in_path(self, mocked_extract_lot_adapter, mocked_decode_path_info):
        path = 'domain/api/0/notLots'
        mocked_extract_lot_adapter.side_effect = ['adapter']
        self.mocked_request.environ = {'PATH_INFO': path}
        mocked_decode_path_info.side_effect = iter([path])

        returned_value = extract_lot(self.mocked_request)
        assert returned_value is None
        assert mocked_decode_path_info.call_count == 1
        assert mocked_extract_lot_adapter.call_count == 0


@mock.patch('openregistry.lots.core.utils.error_handler', autospec=True)
class TestExtractLotAdapter(unittest.TestCase):

    def setUp(self):
        self.mocked_request = mock.MagicMock(
            registry=mock.MagicMock(db=mock.MagicMock()),
            lot_from_data=mock.MagicMock(),
            errors=mock.MagicMock(add=mock.MagicMock())
        )
        self.mocked_request.errors.status = None
        self.lot_id = 'lotID'

        self.mocked_request.registry.db.get = mock.MagicMock()
        self.db = self.mocked_request.registry.db

    def test_when_db_return_none(self, mocked_handler):
        doc = None
        self.db.get.side_effect = iter([doc])
        mocked_handler.side_effect = iter([DummyException])

        with self.assertRaises(DummyException):
            extract_lot_adapter(self.mocked_request, self.lot_id)
        assert self.db.get.call_count == 1
        self.db.get.assert_called_with(self.lot_id)

        assert mocked_handler.call_count == 1
        mocked_handler.assert_called_with(self.mocked_request)

        assert self.mocked_request.errors.add.call_count == 1
        self.mocked_request.errors.add.assert_called_with('url', 'lot_id', 'Not Found')
        assert self.mocked_request.errors.status == 404
        self.mocked_request.errors.status = None

        assert self.mocked_request.lot_from_data.call_count == 0

    def test_db_return_doc_type_not_equal_lot(self, mocked_handler):
        doc = {'doc_type': 'notLot'}
        self.db.get.side_effect = iter([doc])
        mocked_handler.side_effect = iter([DummyException])

        with self.assertRaises(DummyException):
            extract_lot_adapter(self.mocked_request, self.lot_id)

        assert self.db.get.call_count == 1
        self.db.get.assert_called_with(self.lot_id)

        assert mocked_handler.call_count == 1
        mocked_handler.assert_called_with(self.mocked_request)

        assert self.mocked_request.errors.add.call_count == 1
        self.mocked_request.errors.add.assert_called_with('url', 'lot_id', 'Not Found')
        assert self.mocked_request.errors.status == 404
        self.mocked_request.errors.status = None

        assert self.mocked_request.lot_from_data.call_count == 0

    def test_db_return_doc_type_equal_lot(self, mocked_handler):
        doc = {'doc_type': 'Lot'}
        self.db.get.side_effect = iter([doc])
        self.mocked_request.lot_from_data.side_effect = iter(['lotFromData'])
        returned_value = extract_lot_adapter(self.mocked_request, self.lot_id)
        assert returned_value == 'lotFromData'
        assert self.db.get.call_count == 1
        self.db.get.assert_called_with(self.lot_id)

        assert self.mocked_request.errors.add.call_count == 0
        assert self.mocked_request.errors.status is None
        assert mocked_handler.call_count == 0

        assert self.mocked_request.lot_from_data.call_count == 1
        self.mocked_request.lot_from_data.assert_called_with(doc)


@mock.patch('openregistry.lots.core.utils.update_logging_context', autospec=True)
@mock.patch('openregistry.lots.core.utils.error_handler', autospec=True)
class TestLotFromData(unittest.TestCase):

    def setUp(self):
        self.mocked_request = mock.MagicMock(
            registry=mock.MagicMock(
                lotTypes={}
            ),
            errors=mock.MagicMock(add=mock.MagicMock(), status=None)
        )
        self.mocked_request.errors.status = None
        self. mocked_model = mock.MagicMock()
        self.mocked_request.registry.lotTypes['someLotType'] = self.mocked_model

    def test_with_create_true(self, mocked_handler, mocked_update_logging):
        data = {'lotType': 'someLotType'}
        self.mocked_model.side_effect = iter(['model'])
        mocked_handler.side_effect = iter([DummyException])
        returned_value = lot_from_data(self.mocked_request, data)
        assert returned_value == 'model'

        assert mocked_update_logging.call_count == 1
        mocked_update_logging.assert_called_with(self.mocked_request, {'lot_type': data['lotType']})

        assert self.mocked_model.call_count == 1
        self.mocked_model.assert_called_with(data)

        assert mocked_handler.call_count == 0
        assert self.mocked_request.errors.add.call_count == 0
        assert self.mocked_request.errors.status is None

    def test_with_create_false(self, mocked_handler, mocked_update_logging):
        data = {'lotType': 'someLotType'}
        self.mocked_model.side_effect = iter(['model'])
        returned_value = lot_from_data(self.mocked_request, data, create=False)
        assert returned_value == self.mocked_model

        assert mocked_update_logging.call_count == 1
        mocked_update_logging.assert_called_with(self.mocked_request, {'lot_type': data['lotType']})

        assert self.mocked_model.call_count == 0

        assert mocked_handler.call_count == 0
        assert self.mocked_request.errors.add.call_count == 0
        assert self.mocked_request.errors.status is None

    def test_with_wrong_lotType(self, mocked_handler, mocked_update_logging):
        data = {'lotType': 'wrongLotType'}
        self.mocked_model.side_effect = iter(['model'])
        mocked_handler.side_effect = iter([DummyException])

        with self.assertRaises(DummyException):
            lot_from_data(self.mocked_request, data)

        assert mocked_update_logging.call_count == 0

        assert self.mocked_model.call_count == 0

        assert mocked_handler.call_count == 1
        mocked_handler.assert_called_with(self.mocked_request)

        assert self.mocked_request.errors.add.call_count == 1
        self.mocked_request.errors.add.assert_called_with('body', 'lotType', 'Not implemented')
        assert self.mocked_request.errors.status == 415

    def test_with_wrong_lotType_and_raise_false(self, mocked_handler, mocked_update_logging):
        data = {'lotType': 'wrongLotType'}
        self.mocked_model.side_effect = iter(['model'])
        mocked_handler.side_effect = iter([DummyException])

        returned_value = lot_from_data(self.mocked_request, data, raise_error=False)
        assert returned_value is None

        assert mocked_update_logging.call_count == 1
        mocked_update_logging.assert_called_with(self.mocked_request, {'lot_type': data['lotType']})

        assert self.mocked_model.call_count == 0

        assert mocked_handler.call_count == 0

        assert self.mocked_request.errors.add.call_count == 0
        assert self.mocked_request.errors.status is None


class TestRegisterLotType(unittest.TestCase):

    def setUp(self):
        self.mocked_config = mock.MagicMock(
            registry=mock.MagicMock(lotTypes={})
        )
        self.mocked_model = mock.MagicMock(
            lotType=mock.MagicMock(default='lotType')
        )

    def test_register_lotType(self):
        register_lotType(self.mocked_config, self.mocked_model, 'lotType')
        assert self.mocked_config.registry.lotTypes.keys()[0] == self.mocked_model.lotType.default
        assert self.mocked_config.registry.lotTypes[self.mocked_model.lotType.default] == self.mocked_model


@mock.patch('openregistry.lots.core.utils.save_lot', autospec=True)
@mock.patch('openregistry.lots.core.utils.apply_data_patch', autospec=True)
class TestApplyPatch(unittest.TestCase):

    def setUp(self):
        self.mocked_request = mock.MagicMock(validated={})
        self.context = mock.MagicMock()
        self.context.serialize = mock.MagicMock()
        self.context.import_data = mock.MagicMock()
        self.mocked_request.context = self.context

        self.serialized_data = 'serializedData'
        self.patch = 'patch'
        self.saved_lot = 'saved_lot'

    def test_with_default_args(self, mocked_apply_data, mocked_save_lot):
        self.mocked_request.validated['data'] = 'data'
        mocked_apply_data.side_effect = iter([self.patch])
        self.context.serialize.side_effect = iter([self.serialized_data])
        mocked_save_lot.side_effect = iter([self.saved_lot])

        returned_value = apply_patch(self.mocked_request)
        assert returned_value == self.saved_lot

        assert mocked_apply_data.call_count == 1
        mocked_apply_data.assert_called_with(
            self.serialized_data,
            self.mocked_request.validated['data']
        )

        assert self.context.import_data.call_count == 1
        self.context.import_data.assert_called_with(self.patch)

        assert mocked_save_lot.call_count == 1
        mocked_save_lot.assert_called_with(self.mocked_request)

    def test_when_data_not_none(self, mocked_apply_data, mocked_save_lot):
        self.mocked_request.validated = {'data': 'validatedData'}
        data = 'someData'
        mocked_apply_data.side_effect = iter([self.patch])
        self.context.serialize.side_effect = iter([self.serialized_data])
        mocked_save_lot.side_effect = iter([self.saved_lot])

        returned_value = apply_patch(self.mocked_request, data=data)
        assert returned_value == self.saved_lot

        assert mocked_apply_data.call_count == 1
        mocked_apply_data.assert_called_with(self.serialized_data, data)

        assert self.context.import_data.call_count == 1
        self.context.import_data.assert_called_with(self.patch)

        assert mocked_save_lot.call_count == 1
        mocked_save_lot.assert_called_with(self.mocked_request)

    def test_when_src_is_not_none(self, mocked_apply_data, mocked_save_lot):
        src = 'someSrc'
        self.mocked_request.validated['data'] = 'data'
        mocked_apply_data.side_effect = iter([self.patch])
        self.context.serialize.side_effect = iter([self.serialized_data])
        mocked_save_lot.side_effect = iter([self.saved_lot])

        returned_value = apply_patch(self.mocked_request, src=src)
        assert returned_value == self.saved_lot

        assert mocked_apply_data.call_count == 1
        mocked_apply_data.assert_called_with(src, self.mocked_request.validated['data'])

        assert self.context.import_data.call_count == 1
        self.context.import_data.assert_called_with(self.patch)

        assert mocked_save_lot.call_count == 1
        mocked_save_lot.assert_called_with(self.mocked_request)

    def test_when_save_is_false(self, mocked_apply_data, mocked_save_lot):
        self.mocked_request.validated['data'] = 'data'
        mocked_apply_data.side_effect = iter([self.patch])
        self.context.serialize.side_effect = iter([self.serialized_data])
        mocked_save_lot.side_effect = iter([self.saved_lot])

        returned_value = apply_patch(self.mocked_request, save=False)
        assert returned_value is None

        assert mocked_apply_data.call_count == 1
        mocked_apply_data.assert_called_with(self.serialized_data, self.mocked_request.validated['data'])

        assert self.context.import_data.call_count == 1
        self.context.import_data.assert_called_with(self.patch)

        assert mocked_save_lot.call_count == 0

    def test_when_all_data_is_none(self, mocked_apply_data, mocked_save_lot):
        self.mocked_request.validated['data'] = None
        mocked_apply_data.side_effect = iter([self.patch])
        self.context.serialize.side_effect = iter([self.serialized_data])
        mocked_save_lot.side_effect = iter([self.saved_lot])

        returned_value = apply_patch(self.mocked_request)
        assert returned_value is None

        assert mocked_apply_data.call_count == 0

        assert self.context.import_data.call_count == 0

        assert mocked_save_lot.call_count == 0

    def test_when_apply_data_patch_return_none(self, mocked_apply_data, mocked_save_lot):
        self.mocked_request.validated['data'] = 'data'
        mocked_apply_data.side_effect = iter([None])
        self.context.serialize.side_effect = iter([self.serialized_data])
        mocked_save_lot.side_effect = iter([self.saved_lot])

        returned_value = apply_patch(self.mocked_request, save=False)
        assert returned_value is None

        assert mocked_apply_data.call_count == 1
        mocked_apply_data.assert_called_with(
            self.serialized_data,
            self.mocked_request.validated['data']
        )

        assert self.context.import_data.call_count == 0

        assert mocked_save_lot.call_count == 0


class TestLotSerialize(unittest.TestCase):

    def setUp(self):
        self.mocked_request = mock.MagicMock(
            lot_from_data=mock.MagicMock()
        )
        self.mocked_lot = mock.MagicMock(
            serialize=mock.MagicMock()
        )

        self.lot_data = {
            'lotType': 'someLotType',
            'dateModified': 'dateModified',
            'id': 'someID',
            'extra_field': 'extraValue'
        }
        self.fields = self.lot_data.keys()

    def test_when_lot_from_data_return_none(self):
        self.mocked_request.lot_from_data.side_effect = iter([None])
        returned_value = lot_serialize(self.mocked_request, self.lot_data, self.fields)
        assert returned_value['lotType'] == self.lot_data['lotType']
        assert returned_value['dateModified'] == self.lot_data['dateModified']
        assert returned_value['id'] == self.lot_data['id']
        assert bool('extra_field' in returned_value) is False

        assert self.mocked_request.lot_from_data.call_count == 1
        self.mocked_request.lot_from_data.assert_called_with(self.lot_data, raise_error=False)

        assert self.mocked_lot.serialize.call_count == 0

    def test_when_lot_from_data_return_not_none(self):
        lot_serialize_data = {
            'lotType': 'anotherLotType',
            'dateModified': 'anotherDateModified',
            'id': 'anotherID',
            'extra_field': 'anotherExtraValue',
            'second_extra_field': 'secondExtraValue'
        }
        self.mocked_lot.status = 'status'
        self.mocked_lot.serialize.side_effect = iter([lot_serialize_data])
        self.mocked_request.lot_from_data.side_effect = iter([self.mocked_lot])
        returned_value = lot_serialize(self.mocked_request, self.lot_data, self.fields)
        assert returned_value['lotType'] == lot_serialize_data['lotType']
        assert returned_value['dateModified'] == lot_serialize_data['dateModified']
        assert returned_value['id'] == lot_serialize_data['id']
        assert returned_value['extra_field'] == lot_serialize_data['extra_field']
        assert bool('second_extra_field' in returned_value) is False

        assert self.mocked_request.lot_from_data.call_count == 1
        self.mocked_request.lot_from_data.assert_called_with(self.lot_data, raise_error=False)

        assert self.mocked_lot.serialize.call_count == 1
        self.mocked_lot.serialize.assert_called_with(self.mocked_lot.status)


@mock.patch('openregistry.lots.core.utils.get_revision_changes', autospec=True)
@mock.patch('openregistry.lots.core.utils.store_lot', autospec=True)
@mock.patch('openregistry.lots.core.utils.set_modetest_titles', autospec=True)
class TestSaveLot(unittest.TestCase):

    def setUp(self):
        self.mocked_request = mock.MagicMock()
        self.mocked_lot = mock.MagicMock(
            serialize=mock.MagicMock()
        )
        self.lot_src = 'lot_src'
        self.lot_serialize = 'serialized'
        self.patch = 'patch'

    def test_mode_equal_test(self, mocked_set_modetest_titles, mocked_store_lot, mocked_get_revision_changes):
        self.mocked_lot.mode = u'test'
        mocked_get_revision_changes.side_effect = iter([self.patch])
        self.mocked_lot.serialize.side_effect = iter([lot_serialize])
        self.mocked_request.validated = {'lot': self.mocked_lot, 'lot_src': self.lot_src}
        save_lot(self.mocked_request)

        assert mocked_set_modetest_titles.call_count == 1
        mocked_set_modetest_titles.assert_called_with(self.mocked_lot)

        assert mocked_get_revision_changes.call_count == 1
        mocked_get_revision_changes.assert_called_with(lot_serialize, self.lot_src)

        assert self.mocked_lot.serialize.call_count == 1
        self.mocked_lot.serialize.assert_called_with('plain')

        assert mocked_store_lot.call_count == 1
        mocked_store_lot.assert_called_with(self.mocked_lot, self.patch, self.mocked_request)

    def test_mode_equal_notTest(self, mocked_set_modetest_titles, mocked_store_lot, mocked_get_revision_changes):
        self.mocked_lot.mode = u'notTest'
        mocked_get_revision_changes.side_effect = iter([self.patch])
        self.mocked_lot.serialize.side_effect = iter([lot_serialize])
        self.mocked_request.validated = {'lot': self.mocked_lot, 'lot_src': self.lot_src}
        save_lot(self.mocked_request)

        assert mocked_set_modetest_titles.call_count == 0

        assert mocked_get_revision_changes.call_count == 1
        mocked_get_revision_changes.assert_called_with(lot_serialize, self.lot_src)

        assert self.mocked_lot.serialize.call_count == 1
        self.mocked_lot.serialize.assert_called_with('plain')

        assert mocked_store_lot.call_count == 1
        mocked_store_lot.assert_called_with(self.mocked_lot, self.patch, self.mocked_request)

    def test_when_get_revision_changes_return_none(self, mocked_set_modetest_titles, mocked_store_lot, mocked_get_revision_changes):
        self.mocked_lot.mode = u'notTest'
        mocked_get_revision_changes.side_effect = iter([None])
        self.mocked_lot.serialize.side_effect = iter([lot_serialize])
        self.mocked_request.validated = {'lot': self.mocked_lot, 'lot_src': self.lot_src}
        save_lot(self.mocked_request)

        assert mocked_set_modetest_titles.call_count == 0

        assert mocked_get_revision_changes.call_count == 1
        mocked_get_revision_changes.assert_called_with(lot_serialize, self.lot_src)

        assert self.mocked_lot.serialize.call_count == 1
        self.mocked_lot.serialize.assert_called_with('plain')

        assert mocked_store_lot.call_count == 0


class TestSubscribersPicker(unittest.TestCase):

    def setUp(self):
        self.value = 'value'
        self.mocked_event = mock.MagicMock()
        self.mocked_lot = mock.MagicMock()
        self.subscriber_picker = SubscribersPicker(self.value, {})

    def test_init_SubscribersPicker(self):
        assert self.subscriber_picker.val == self.value
        assert self.subscriber_picker.text() == 'lotType = {}'.format(self.value)

    def test_event_lot_is_none(self):
        self.mocked_event.lot = None
        assert self.subscriber_picker(self.mocked_event) is False

    def test_event_lot_is_not_none_and_lotType_not_equal_value(self):
        self.mocked_lot.lotType = 'wrong'
        self.mocked_event.lot = self.mocked_lot
        assert self.subscriber_picker(self.mocked_event) is False

    def test_event_lot_is_not_none_and_lotType_equal_value(self):
        self.mocked_lot._internal_type = self.subscriber_picker.val
        self.mocked_event.lot = self.mocked_lot
        assert self.subscriber_picker(self.mocked_event) is True


class TestIsLot(unittest.TestCase):

    def setUp(self):
        self.value = 'value'
        self.mocked_request = mock.MagicMock()
        self.mocked_lot = mock.MagicMock()
        self.is_lot_instance = isLot(self.value, {})

    def test_init_isLot(self):
        assert self.is_lot_instance.val == self.value
        assert self.is_lot_instance.text() == 'lotType = {}'.format(self.value)

    def test_request_lot_is_none(self):
        self.mocked_request.lot = None
        assert self.is_lot_instance({}, self.mocked_request) is False

    def test_request_lot_is_not_none_and_lotType_not_equal_value(self):
        self.mocked_lot.lotType = 'wrong'
        self.mocked_request.lot = self.mocked_lot
        assert self.is_lot_instance({}, self.mocked_request) is False

    def test_request_lot_is_not_none_and_lotType_equal_value(self):
        self.mocked_lot.lotType = 'someValue'
        self.mocked_request.lot = self.mocked_lot
        self.mocked_request.registry.lot_type_configurator = {'someValue': 'value'}
        assert self.is_lot_instance({}, self.mocked_request) is True

    def test_get_lot_types(self):
        self.mocked_lot.lotType = 'someValue'
        self.mocked_request.lot = self.mocked_lot
        self.mocked_request.registry.lot_type_configurator = {'someValue': 'value'}
        lots = get_lot_types(self.mocked_request.registry, ('value',))
        assert lots == ['someValue']


@mock.patch('openregistry.lots.core.utils.context_unpack', autospec=True)
@mock.patch('openregistry.lots.core.utils.LOGGER', autospec=True)
@mock.patch('openregistry.lots.core.tests.utils.Lot.revisions')
@mock.patch('openregistry.lots.core.utils.prepare_revision', autospec=True)
@mock.patch('openregistry.lots.core.utils.get_now', autospec=True)
class TestStoreLot(unittest.TestCase):

    def setUp(self):
        self.lot = Lot()

        self.mocked_request = mock.MagicMock()
        self.mocked_request.authenticated_userid = 'authID'
        self.mocked_request.registry.db = 'db'
        self.mocked_request.errors = mock.MagicMock()
        self.mocked_request.errors.status = None
        self.mocked_request.errors.add = mock.MagicMock()

        self.patch = 'patch'
        self.new_rev = 'new_revision'
        self.rev_data = 'some data for new revision'

        self.old_date = datetime.now() - timedelta(days=5)
        self.new_date = datetime.now()
        self.unpacked_context = 'unpacked context'

    def test_success_storing_in_db(self, mocked_get_now, mocked_prepare_revision, mocked_lot_revisions, mocked_logger, mocked_context_unpack):
        with mock.patch.object(self.lot, 'store', autospec=True) as mocked_store:
            with mock.patch.object(self.lot, 'revisions') as revisions_mock:
                self.lot.dateModified = self.old_date
                mocked_context_unpack.side_effect = iter([
                    self.unpacked_context
                ])
                mocked_get_now.side_effect = iter([
                    self.new_date
                ])
                mocked_lot_revisions.model_class.side_effect = iter([self.new_rev])
                mocked_prepare_revision.side_effect = iter([self.rev_data])

                assert store_lot(self.lot, self.patch, self.mocked_request) is True

                assert mocked_prepare_revision.call_count == 1
                mocked_prepare_revision.assert_called_with(
                    self.lot,
                    self.patch,
                    self.mocked_request.authenticated_userid
                )

                assert mocked_get_now.call_count == 1

                assert mocked_lot_revisions.model_class.call_count == 1
                mocked_lot_revisions.model_class.assert_called_with(self.rev_data)

                assert revisions_mock.append.call_count == 1
                revisions_mock.append.assert_called_with(self.new_rev)

                assert mocked_store.call_count == 1
                mocked_store.assert_called_with(self.mocked_request.registry.db)

                assert mocked_logger.info.call_count == 1
                mocked_logger.info.assert_called_with(
                    'Saved lot {lot_id}: dateModified {old_dateModified} -> {new_dateModified}'.format(
                        lot_id=self.lot.id,
                        old_dateModified=self.old_date.isoformat(),
                        new_dateModified=self.new_date.isoformat()),
                    extra=self.unpacked_context
                )

                assert self.mocked_request.errors.add.call_count == 0
                assert self.mocked_request.errors.status is None

    def test_model_validation_error(self, mocked_get_now, mocked_prepare_revision, mocked_lot_revisions, mocked_logger, mocked_context_unpack):
        with mock.patch.object(self.lot, 'store', autospec=True) as mocked_store:
            with mock.patch.object(self.lot, 'revisions') as revisions_mock:
                self.lot.dateModified = self.old_date

                mocked_get_now.side_effect = iter([
                    self.new_date
                ])
                mocked_lot_revisions.model_class.side_effect = iter([self.new_rev])
                mocked_prepare_revision.side_effect = iter([self.rev_data])

                error_key = 'error'
                error_message = 'Some error'
                mocked_store.side_effect = iter([
                    ModelValidationError({error_key: error_message})
                ])
                assert store_lot(self.lot, self.patch, self.mocked_request) is None

                mocked_prepare_revision.assert_called_with(
                    self.lot,
                    self.patch,
                    self.mocked_request.authenticated_userid
                )

                assert mocked_get_now.call_count == 1

                assert mocked_lot_revisions.model_class.call_count == 1
                mocked_lot_revisions.model_class.assert_called_with(self.rev_data)

                assert revisions_mock.append.call_count == 1
                revisions_mock.append.assert_called_with(self.new_rev)

                assert mocked_store.call_count == 1
                mocked_store.assert_called_with(self.mocked_request.registry.db)

                assert self.mocked_request.errors.add.call_count == 1
                assert self.mocked_request.errors.status == 422
                self.mocked_request.errors.add.assert_called_with('body', error_key, error_message)

                assert mocked_logger.info.call_count == 0

    def test_resource_conflict(self, mocked_get_now, mocked_prepare_revision, mocked_lot_revisions, mocked_logger, mocked_context_unpack):
        with mock.patch.object(self.lot, 'store', autospec=True) as mocked_store:
            with mock.patch.object(self.lot, 'revisions') as revisions_mock:
                self.lot.dateModified = self.old_date

                mocked_get_now.side_effect = iter([
                    self.new_date
                ])
                mocked_lot_revisions.model_class.side_effect = iter([self.new_rev])
                mocked_prepare_revision.side_effect = iter([self.rev_data])

                error_message = 'conflict error'
                mocked_store.side_effect = iter([
                    ResourceConflict(error_message)
                ])
                assert store_lot(self.lot, self.patch, self.mocked_request) is None

                mocked_prepare_revision.assert_called_with(
                    self.lot,
                    self.patch,
                    self.mocked_request.authenticated_userid
                )
                assert mocked_get_now.call_count == 1

                assert mocked_lot_revisions.model_class.call_count == 1
                mocked_lot_revisions.model_class.assert_called_with(self.rev_data)

                assert revisions_mock.append.call_count == 1
                revisions_mock.append.assert_called_with(self.new_rev)

                assert mocked_store.call_count == 1
                mocked_store.assert_called_with(self.mocked_request.registry.db)

                assert self.mocked_request.errors.add.call_count == 1
                assert self.mocked_request.errors.status == 409
                self.mocked_request.errors.add.assert_called_with('body', 'data', error_message)

                assert mocked_logger.info.call_count == 0

    def test_exception(self, mocked_get_now, mocked_prepare_revision, mocked_lot_revisions, mocked_logger, mocked_context_unpack):
        with mock.patch.object(self.lot, 'store', autospec=True) as mocked_store:
            with mock.patch.object(self.lot, 'revisions') as revisions_mock:
                self.lot.dateModified = self.old_date

                mocked_get_now.side_effect = iter([
                    self.new_date
                ])
                mocked_lot_revisions.model_class.side_effect = iter([self.new_rev])
                mocked_prepare_revision.side_effect = iter([self.rev_data])

                error_message = 'just exception'
                mocked_store.side_effect = iter([
                    Exception(error_message)
                ])
                assert store_lot(self.lot, self.patch, self.mocked_request) is None

                mocked_prepare_revision.assert_called_with(
                    self.lot,
                    self.patch,
                    self.mocked_request.authenticated_userid
                )

                assert mocked_lot_revisions.model_class.call_count == 1
                mocked_lot_revisions.model_class.assert_called_with(self.rev_data)

                assert revisions_mock.append.call_count == 1
                revisions_mock.append.assert_called_with(self.new_rev)

                assert mocked_store.call_count == 1
                mocked_store.assert_called_with(self.mocked_request.registry.db)

                assert self.mocked_request.errors.add.call_count == 1
                assert self.mocked_request.errors.status is None
                self.mocked_request.errors.add.assert_called_with('body', 'data', error_message)

                assert mocked_logger.info.call_count == 0

    def test_modified_is_false(self, mocked_get_now, mocked_prepare_revision, mocked_lot_revisions, mocked_logger, mocked_context_unpack):
        with mock.patch.object(self.lot, 'store', autospec=True) as mocked_store:
            with mock.patch.object(self.lot, 'revisions') as revisions_mock:
                self.lot.modified = False
                self.lot.dateModified = self.old_date

                mocked_context_unpack.side_effect = iter([
                    self.unpacked_context
                ])
                mocked_get_now.side_effect = iter([
                    self.new_date
                ])
                mocked_store.side_effect = iter([
                    None
                ])
                mocked_lot_revisions.model_class.side_effect = iter([self.new_rev])
                mocked_prepare_revision.side_effect = iter([self.rev_data])

                assert store_lot(self.lot, self.patch, self.mocked_request) is True

                assert mocked_prepare_revision.call_count == 1
                mocked_prepare_revision.assert_called_with(
                    self.lot,
                    self.patch,
                    self.mocked_request.authenticated_userid
                )

                assert mocked_get_now.call_count == 0

                assert mocked_lot_revisions.model_class.call_count == 1
                mocked_lot_revisions.model_class.assert_called_with(self.rev_data)

                assert revisions_mock.append.call_count == 1
                revisions_mock.append.assert_called_with(self.new_rev)

                assert mocked_store.call_count == 1
                mocked_store.assert_called_with(self.mocked_request.registry.db)

                assert mocked_logger.info.call_count == 1
                mocked_logger.info.assert_called_with(
                    'Saved lot {lot_id}: dateModified {old_dateModified} -> {new_dateModified}'.format(
                        lot_id=self.lot.id,
                        old_dateModified=self.old_date.isoformat(),
                        new_dateModified=self.old_date.isoformat()),
                    extra=self.unpacked_context
                )


@mock.patch('openregistry.lots.core.utils.project_configurator', autospec=True)
class TestLotProjectConfigurator(BaseLotWebTest):

    def setUp(self):
        self.database = self.db

    def test_generate_id(self, mock_project_configurator):
        test_prefix = 'TEST-ID'
        mock_project_configurator.LOT_PREFIX = test_prefix
        result = generate_lot_id(get_now(), self.db)

        key = get_now().date().isoformat()
        index = self.db.get(key, 1)
        mock_id = '{}-{:04}-{:02}-{:02}-{:06}{}'.format(
            test_prefix,
            get_now().year,
            get_now().month,
            get_now().day,
            index,
            ''
        )
        self.assertEqual(result, mock_id)
