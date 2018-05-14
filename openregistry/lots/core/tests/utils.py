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
    store_lot

)
from openregistry.lots.core.models import Lot
from openregistry.lots.core.tests.base import DummyException

now = get_now()


class DummyUtilityTest(unittest.TestCase):

    def test_generate_lot_id(self):
        ctime = datetime.now()
        mocked_key = ctime.date().isoformat()
        server_id = '1'
        db = mock.MagicMock()
        db.get = mock.MagicMock()
        db.save = mock.MagicMock()


        # LotID with set server_id
        index = 1
        db.get.side_effect = iter([{}])
        mocked_lotIDdoc = 'lotID_' + server_id
        mocked_lotID = {mocked_key: 2}
        lot_id = 'UA-LR-DGF-{:04}-{:02}-{:02}-{:06}{}'.format(
                                                ctime.year,
                                                ctime.month,
                                                ctime.day,
                                                index,
                                                '-' + server_id
                                            )

        returned_lot_id = generate_lot_id(ctime, db, server_id)
        assert lot_id == returned_lot_id
        assert db.get.call_count == 1
        db.get.assert_called_with(mocked_lotIDdoc, {'_id': mocked_lotIDdoc})
        assert db.save.call_count == 1
        db.save.assert_called_with(mocked_lotID)

        # LotID without server_id
        index = 1
        db.get.side_effect = iter([{}])
        mocked_lotIDdoc = 'lotID'
        mocked_lotID = {mocked_key: 2}
        lot_id = 'UA-LR-DGF-{:04}-{:02}-{:02}-{:06}{}'.format(
                                                ctime.year,
                                                ctime.month,
                                                ctime.day,
                                                index,
                                                ''
                                            )

        returned_lot_id = generate_lot_id(ctime, db)
        assert lot_id == returned_lot_id
        assert db.get.call_count == 2
        db.get.assert_called_with(mocked_lotIDdoc, {'_id': mocked_lotIDdoc})
        assert db.save.call_count == 2
        db.save.assert_called_with(mocked_lotID)

        # LotID without server_id and with index
        index = 2
        db.get.side_effect = iter([{mocked_key: index}])
        mocked_lotIDdoc = 'lotID'
        mocked_lotID = {mocked_key: index + 1}
        lot_id = 'UA-LR-DGF-{:04}-{:02}-{:02}-{:06}{}'.format(
                                                ctime.year,
                                                ctime.month,
                                                ctime.day,
                                                index,
                                                ''
                                            )

        returned_lot_id = generate_lot_id(ctime, db)
        assert lot_id == returned_lot_id
        assert db.get.call_count == 3
        db.get.assert_called_with(mocked_lotIDdoc, {'_id': mocked_lotIDdoc})
        assert db.save.call_count == 3
        db.save.assert_called_with(mocked_lotID)

        # Check while loop
        db.get.side_effect = iter([{}, {}, {}])
        db.save.side_effect = iter([DummyException, ResourceConflict, None])
        generate_lot_id(ctime, db)
        assert db.get.call_count == 6
        assert db.save.call_count == 6

    @mock.patch('openregistry.lots.core.utils.decode_path_info', autospec=True)
    @mock.patch('openregistry.lots.core.utils.extract_lot_adapter', autospec=True)
    def test_extract_lot(self, mocked_extract_lot_adapter, mocked_decode_path_info):
        mocked_request = mock.MagicMock()
        mocked_request.environ = {}

        # Check with KeyError
        mocked_extract_lot_adapter.side_effect = iter(['adapter'])
        returned_value = extract_lot(mocked_request)
        assert returned_value is None
        assert mocked_extract_lot_adapter.call_count == 0
        assert mocked_decode_path_info.call_count == 0

        # Check with path with id
        path = 'domain/api/0/lots/lotID'
        mocked_extract_lot_adapter.side_effect = iter(['adapter'])
        mocked_request.environ = {'PATH_INFO': path}
        mocked_decode_path_info.side_effect = iter([path])

        returned_value = extract_lot(mocked_request)

        assert returned_value == 'adapter'
        assert mocked_decode_path_info.call_count == 1
        assert mocked_extract_lot_adapter.call_count == 1
        mocked_extract_lot_adapter.assert_called_with(mocked_request, path.split('/')[4])


        # Check with path without len less 4
        path = 'domain/api/0/'
        mocked_extract_lot_adapter.side_effect = ['adapter']
        mocked_request.environ = {'PATH_INFO': path}
        mocked_decode_path_info.side_effect = iter([path])

        returned_value = extract_lot(mocked_request)
        assert returned_value is None
        assert mocked_decode_path_info.call_count == 2
        assert mocked_extract_lot_adapter.call_count == 1

        # Check with path without lots in path
        path = 'domain/api/0/notLots'
        mocked_extract_lot_adapter.side_effect = ['adapter']
        mocked_request.environ = {'PATH_INFO': path}
        mocked_decode_path_info.side_effect = iter([path])

        returned_value = extract_lot(mocked_request)
        assert returned_value is None
        assert mocked_decode_path_info.call_count == 3
        assert mocked_extract_lot_adapter.call_count == 1

    @mock.patch('openregistry.lots.core.utils.error_handler', autospec=True)
    def test_extract_lot_adapter(self, mocked_handler):
        mocked_request = mock.MagicMock(
            registry=mock.MagicMock(db=mock.MagicMock()),
            lot_from_data=mock.MagicMock(),
            errors=mock.MagicMock(add=mock.MagicMock())
        )
        lot_id = 'lotID'

        mocked_request.registry.db.get = mock.MagicMock()
        db = mocked_request.registry.db
        # Check if db return None
        doc = None
        db.get.side_effect = iter([doc])
        mocked_handler.side_effect = iter([DummyException])

        with self.assertRaises(DummyException):
            extract_lot_adapter(mocked_request, lot_id)
        assert db.get.call_count == 1
        db.get.assert_called_with(lot_id)

        assert mocked_handler.call_count == 1
        mocked_handler.assert_called_with(mocked_request)

        assert mocked_request.errors.add.call_count == 1
        mocked_request.errors.add.assert_called_with('url', 'lot_id', 'Not Found')
        assert mocked_request.errors.status == 404
        mocked_request.errors.status = None

        assert mocked_request.lot_from_data.call_count == 0

        # Check if db return doc_type != Lot
        doc = {'doc_type': 'notLot'}
        db.get.side_effect = iter([doc])
        mocked_handler.side_effect = iter([DummyException])

        with self.assertRaises(DummyException):
            extract_lot_adapter(mocked_request, lot_id)

        assert db.get.call_count == 2
        db.get.assert_called_with(lot_id)

        assert mocked_handler.call_count == 2
        mocked_handler.assert_called_with(mocked_request)

        assert mocked_request.errors.add.call_count == 2
        mocked_request.errors.add.assert_called_with('url', 'lot_id', 'Not Found')
        assert mocked_request.errors.status == 404
        mocked_request.errors.status = None

        assert mocked_request.lot_from_data.call_count == 0

        # Check if db return doc_type == Lot
        doc = {'doc_type': 'Lot'}
        db.get.side_effect = iter([doc])
        mocked_request.lot_from_data.side_effect = iter(['lotFromData'])
        returned_value = extract_lot_adapter(mocked_request, lot_id)
        assert returned_value == 'lotFromData'
        assert db.get.call_count == 3
        db.get.assert_called_with(lot_id)

        assert mocked_request.errors.add.call_count == 2
        assert mocked_request.errors.status is None
        assert mocked_handler.call_count == 2

        assert mocked_request.lot_from_data.call_count == 1
        mocked_request.lot_from_data.assert_called_with(doc)


    @mock.patch('openregistry.lots.core.utils.update_logging_context', autospec=True)
    @mock.patch('openregistry.lots.core.utils.error_handler', autospec=True)
    def test_lot_from_data(self, mocked_handler, mocked_update_logging):
        mocked_request = mock.MagicMock(
            registry=mock.MagicMock(
                lotTypes={}
            ),
            errors=mock.MagicMock(add=mock.MagicMock(), status=None)
        )
        mocked_model = mock.MagicMock()
        mocked_request.registry.lotTypes['someLotType'] = mocked_model

        # Check lot_from_data with create=True
        data = {'lotType': 'someLotType'}
        mocked_model.side_effect = iter(['model'])
        mocked_handler.side_effect = iter([DummyException])
        returned_value = lot_from_data(mocked_request, data)
        assert returned_value == 'model'

        assert mocked_update_logging.call_count == 1
        mocked_update_logging.assert_called_with(mocked_request, {'lot_type': data['lotType']})

        assert mocked_model.call_count == 1
        mocked_model.assert_called_with(data)

        assert mocked_handler.call_count == 0
        assert mocked_request.errors.add.call_count == 0
        assert mocked_request.errors.status is None

        # Check lot_from_data with create=False
        data = {'lotType': 'someLotType'}
        mocked_model.side_effect = iter(['model'])
        returned_value = lot_from_data(mocked_request, data, create=False)
        assert returned_value == mocked_model

        assert mocked_update_logging.call_count == 2
        mocked_update_logging.assert_called_with(mocked_request, {'lot_type': data['lotType']})

        assert mocked_model.call_count == 1

        assert mocked_handler.call_count == 0
        assert mocked_request.errors.add.call_count == 0
        assert mocked_request.errors.status is None

        # Check lot_from_data with wrong lotType
        data = {'lotType': 'wrongLotType'}
        mocked_model.side_effect = iter(['model'])
        mocked_handler.side_effect = iter([DummyException])

        with self.assertRaises(DummyException):
            lot_from_data(mocked_request, data)

        assert mocked_update_logging.call_count == 2

        assert mocked_model.call_count == 1

        assert mocked_handler.call_count == 1
        mocked_handler.assert_called_with(mocked_request)

        assert mocked_request.errors.add.call_count == 1
        mocked_request.errors.add.assert_called_with('body', 'lotType', 'Not implemented')
        assert mocked_request.errors.status == 415
        mocked_request.errors.status = None

        # Check lot_from_data with wrong lotType and with raise_error False
        data = {'lotType': 'wrongLotType'}
        mocked_model.side_effect = iter(['model'])
        mocked_handler.side_effect = iter([DummyException])

        returned_value = lot_from_data(mocked_request, data, raise_error=False)
        assert returned_value is None

        assert mocked_update_logging.call_count == 3
        mocked_update_logging.assert_called_with(mocked_request, {'lot_type': data['lotType']})

        assert mocked_model.call_count == 1

        assert mocked_handler.call_count == 1
        mocked_handler.assert_called_with(mocked_request)

        assert mocked_request.errors.add.call_count == 1
        assert mocked_request.errors.status is None

    def test_register_lotType(self):
        mocked_config = mock.MagicMock(
            registry=mock.MagicMock(lotTypes={})
        )
        mocked_model = mock.MagicMock(
            lotType=mock.MagicMock(default='default')
        )
        register_lotType(mocked_config, mocked_model)
        assert mocked_config.registry.lotTypes.keys()[0] == mocked_model.lotType.default
        assert mocked_config.registry.lotTypes[mocked_model.lotType.default] == mocked_model

    @mock.patch('openregistry.lots.core.utils.save_lot', autospec=True)
    @mock.patch('openregistry.lots.core.utils.apply_data_patch', autospec=True)
    def test_apply_patch(self, mocked_apply_data, mocked_save_lot):
        mocked_request = mock.MagicMock(validated={})
        context = mock.MagicMock()
        context.serialize = mock.MagicMock()
        context.import_data = mock.MagicMock()
        mocked_request.context = context

        serialized_data = 'serializedData'
        patch = 'patch'
        saved_lot = 'saved_lot'

        # Check apply_patch if data is None save is True src is None
        mocked_request.validated['data'] = 'data'
        mocked_apply_data.side_effect = iter([patch])
        context.serialize.side_effect = iter([serialized_data])
        mocked_save_lot.side_effect = iter([saved_lot])

        returned_value = apply_patch(mocked_request)
        assert returned_value == saved_lot

        assert mocked_apply_data.call_count == 1
        mocked_apply_data.assert_called_with(serialized_data, mocked_request.validated['data'])

        assert context.import_data.call_count == 1
        context.import_data.assert_called_with(patch)

        assert mocked_save_lot.call_count == 1
        mocked_save_lot.assert_called_with(mocked_request)

        # Check apply_patch if data is not None
        mocked_request.validated = {'data': 'validatedData'}
        data = 'someData'
        mocked_apply_data.side_effect = iter([patch])
        context.serialize.side_effect = iter([serialized_data])
        mocked_save_lot.side_effect = iter([saved_lot])

        returned_value = apply_patch(mocked_request, data=data)
        assert returned_value == saved_lot

        assert mocked_apply_data.call_count == 2
        mocked_apply_data.assert_called_with(serialized_data, data)

        assert context.import_data.call_count == 2
        context.import_data.assert_called_with(patch)

        assert mocked_save_lot.call_count == 2
        mocked_save_lot.assert_called_with(mocked_request)

        # Check apply_patch if src is not None
        src = 'someSrc'
        mocked_request.validated['data'] = 'data'
        mocked_apply_data.side_effect = iter([patch])
        context.serialize.side_effect = iter([serialized_data])
        mocked_save_lot.side_effect = iter([saved_lot])

        returned_value = apply_patch(mocked_request, src=src)
        assert returned_value == saved_lot

        assert mocked_apply_data.call_count == 3
        mocked_apply_data.assert_called_with(src, mocked_request.validated['data'])

        assert context.import_data.call_count == 3
        context.import_data.assert_called_with(patch)

        assert mocked_save_lot.call_count == 3
        mocked_save_lot.assert_called_with(mocked_request)

        # Check apply_patch if save is False
        mocked_request.validated['data'] = 'data'
        mocked_apply_data.side_effect = iter([patch])
        context.serialize.side_effect = iter([serialized_data])
        mocked_save_lot.side_effect = iter([saved_lot])

        returned_value = apply_patch(mocked_request, save=False)
        assert returned_value is None

        assert mocked_apply_data.call_count == 4
        mocked_apply_data.assert_called_with(serialized_data, mocked_request.validated['data'])

        assert context.import_data.call_count == 4
        context.import_data.assert_called_with(patch)

        assert mocked_save_lot.call_count == 3

        # Check apply_patch if all data is None
        mocked_request.validated['data'] = None
        mocked_apply_data.side_effect = iter([patch])
        context.serialize.side_effect = iter([serialized_data])
        mocked_save_lot.side_effect = iter([saved_lot])

        returned_value = apply_patch(mocked_request)
        assert returned_value is None

        assert mocked_apply_data.call_count == 4

        assert context.import_data.call_count == 4
        context.import_data.assert_called_with(patch)

        assert mocked_save_lot.call_count == 3

        # Check apply_patch if apply_data_patch return None
        mocked_request.validated['data'] = 'data'
        mocked_apply_data.side_effect = iter([None])
        context.serialize.side_effect = iter([serialized_data])
        mocked_save_lot.side_effect = iter([saved_lot])

        returned_value = apply_patch(mocked_request, save=False)
        assert returned_value is None

        assert mocked_apply_data.call_count == 5
        mocked_apply_data.assert_called_with(serialized_data, mocked_request.validated['data'])

        assert context.import_data.call_count == 4
        context.import_data.assert_called_with(patch)

        assert mocked_save_lot.call_count == 3

    def test_lot_serialize(self):
        mocked_request = mock.MagicMock(
            lot_from_data=mock.MagicMock()
        )
        mocked_lot = mock.MagicMock(
            serialize=mock.MagicMock()
        )

        lot_data = {
            'lotType': 'someLotType',
            'dateModified': 'dateModified',
            'id': 'someID',
            'extra_field': 'extraValue'
        }
        fields = lot_data.keys()

        # Check if request.lot_from_data returned None
        mocked_request.lot_from_data.side_effect = iter([None])
        returned_value = lot_serialize(mocked_request, lot_data, fields)
        assert returned_value['lotType'] == lot_data['lotType']
        assert returned_value['dateModified'] == lot_data['dateModified']
        assert returned_value['id'] == lot_data['id']
        assert bool('extra_field' in returned_value) is False

        assert mocked_request.lot_from_data.call_count == 1
        mocked_request.lot_from_data.assert_called_with(lot_data, raise_error=False)

        # Check if request.lot_from_data returned not None
        lot_serialize_data = {
            'lotType': 'anotherLotType',
            'dateModified': 'anotherDateModified',
            'id': 'anotherID',
            'extra_field': 'anotherExtraValue',
            'second_extra_field': 'secondExtraValue'
        }
        mocked_lot.status = 'status'
        mocked_lot.serialize.side_effect = iter([lot_serialize_data])
        mocked_request.lot_from_data.side_effect = iter([mocked_lot])
        returned_value = lot_serialize(mocked_request, lot_data, fields)
        assert returned_value['lotType'] == lot_serialize_data['lotType']
        assert returned_value['dateModified'] == lot_serialize_data['dateModified']
        assert returned_value['id'] == lot_serialize_data['id']
        assert returned_value['extra_field'] == lot_serialize_data['extra_field']
        assert bool('second_extra_field' in returned_value) is False

        assert mocked_request.lot_from_data.call_count == 2
        mocked_request.lot_from_data.assert_called_with(lot_data, raise_error=False)

        assert mocked_lot.serialize.call_count == 1
        mocked_lot.serialize.assert_called_with(mocked_lot.status)

    @mock.patch('openregistry.lots.core.utils.get_revision_changes', autospec=True)
    @mock.patch('openregistry.lots.core.utils.store_lot', autospec=True)
    @mock.patch('openregistry.lots.core.utils.set_modetest_titles', autospec=True)
    def test_save_lot(self, mocked_set_modetest_titles, mocked_store_lot, mocked_get_revision_changes):
        mocked_request = mock.MagicMock()
        mocked_lot = mock.MagicMock(
            serialize=mock.MagicMock()
        )
        lot_src = 'lot_src'
        lot_serialize = 'serialized'
        patch = 'patch'
        # Check if mode == 'test'
        mocked_lot.mode = u'test'
        mocked_get_revision_changes.side_effect = iter([patch])
        mocked_lot.serialize.side_effect = iter([lot_serialize])
        mocked_request.validated = {'lot': mocked_lot, 'lot_src': lot_src}
        save_lot(mocked_request)

        assert mocked_set_modetest_titles.call_count == 1
        mocked_set_modetest_titles.assert_called_with(mocked_lot)

        assert mocked_get_revision_changes.call_count == 1
        mocked_get_revision_changes.assert_called_with(lot_serialize, lot_src)

        assert mocked_store_lot.call_count == 1
        mocked_store_lot.assert_called_with(mocked_lot, patch, mocked_request)

        assert mocked_lot.serialize.call_count == 1
        mocked_lot.serialize.assert_called_with('plain')

        # Check if mode == 'notTest'
        mocked_lot.mode = u'notTest'
        mocked_get_revision_changes.side_effect = iter([patch])
        mocked_lot.serialize.side_effect = iter([lot_serialize])
        mocked_request.validated = {'lot': mocked_lot, 'lot_src': lot_src}
        save_lot(mocked_request)

        assert mocked_set_modetest_titles.call_count == 1

        assert mocked_get_revision_changes.call_count == 2
        mocked_get_revision_changes.assert_called_with(lot_serialize, lot_src)

        assert mocked_store_lot.call_count == 2
        mocked_store_lot.assert_called_with(mocked_lot, patch, mocked_request)

        assert mocked_lot.serialize.call_count == 2
        mocked_lot.serialize.assert_called_with('plain')

        # Check get_revision_changes returned None
        mocked_lot.mode = u'notTest'
        mocked_get_revision_changes.side_effect = iter([None])
        mocked_lot.serialize.side_effect = iter([lot_serialize])
        mocked_request.validated = {'lot': mocked_lot, 'lot_src': lot_src}
        save_lot(mocked_request)

        assert mocked_set_modetest_titles.call_count == 1

        assert mocked_get_revision_changes.call_count == 3
        mocked_get_revision_changes.assert_called_with(lot_serialize, lot_src)

        assert mocked_lot.serialize.call_count == 3
        mocked_lot.serialize.assert_called_with('plain')

        assert mocked_store_lot.call_count == 2
        mocked_store_lot.assert_called_with(mocked_lot, patch, mocked_request)

    def test_SubscribersPicker(self):
        value = 'value'
        subscriber_picker = SubscribersPicker(value, {})

        assert subscriber_picker.val == value
        assert subscriber_picker.text() == 'lotType = {}'.format(value)

        mocked_event = mock.MagicMock()
        mocked_lot = mock.MagicMock()

        # Check if request.lot is None
        mocked_event.lot = None
        assert subscriber_picker(mocked_event) is False

        # Check if request.lot is not None, but lotType != self.val
        mocked_lot.lotType = 'wrong'
        mocked_event.lot = mocked_lot
        assert subscriber_picker(mocked_event) is False

        # Check if request.lot is not None, but lotType != self.val
        mocked_lot.lotType = subscriber_picker.val
        mocked_event.lot = mocked_lot
        assert subscriber_picker(mocked_event) is True

    def test_isLot(self):
        value = 'value'
        is_lot_instance = isLot(value, {})

        assert is_lot_instance.val == value
        assert is_lot_instance.text() == 'lotType = {}'.format(value)

        mocked_request = mock.MagicMock()
        mocked_lot = mock.MagicMock()

        # Check if request.lot is None
        mocked_request.lot = None
        assert is_lot_instance({}, mocked_request) is False

        # Check if request.lot is not None, but lotType != self.val
        mocked_lot.lotType = 'wrong'
        mocked_request.lot = mocked_lot
        assert is_lot_instance({}, mocked_request) is False

        # Check if request.lot is not None, but lotType != self.val
        mocked_lot.lotType = is_lot_instance.val
        mocked_request.lot = mocked_lot
        assert is_lot_instance({}, mocked_request) is True

    @mock.patch('openregistry.lots.core.utils.context_unpack', autospec=True)
    @mock.patch('openregistry.lots.core.utils.LOGGER', autospec=True)
    @mock.patch('openregistry.lots.core.tests.utils.Lot.revisions')
    @mock.patch('openregistry.lots.core.utils.prepare_revision', autospec=True)
    @mock.patch('openregistry.lots.core.utils.get_now', autospec=True)
    def test_store_lot(self, mocked_get_now, mocked_prepare_revision, mocked_lot_revisions, mocked_logger, mocked_context_unpack):
        lot = Lot()
        # lot.store = mock.MagicMock()
        # lot.revisions = mock.MagicMock()

        mocked_request = mock.MagicMock()
        mocked_request.authenticated_userid = 'authID'
        mocked_request.registry.db = 'db'
        mocked_request.errors = mock.MagicMock()
        mocked_request.errors.add = mock.MagicMock()

        patch = 'patch'
        new_rev = 'new_revision'
        rev_data = 'some data for new revision'

        old_date = datetime.now() - timedelta(days=5)
        new_date = datetime.now()
        unpacked_context = 'unpacked context'

        # Check success storing in db

        lot.dateModified = old_date

        with mock.patch.object(lot, 'store', autospec=True) as mocked_store:
            with mock.patch.object(lot, 'revisions') as revisions_mock:
                # Check success storing in db

                mocked_context_unpack.side_effect = iter([
                    unpacked_context
                ])
                mocked_get_now.side_effect = iter([
                    new_date
                ])
                mocked_lot_revisions.model_class.side_effect = iter([new_rev])
                mocked_prepare_revision.side_effect = iter([rev_data])

                assert store_lot(lot, patch, mocked_request) is True

                assert mocked_prepare_revision.call_count == 1
                mocked_prepare_revision.assert_called_with(
                    lot,
                    patch,
                    mocked_request.authenticated_userid
                )

                assert mocked_lot_revisions.model_class.call_count == 1
                mocked_lot_revisions.model_class.assert_called_with(rev_data)

                assert revisions_mock.append.call_count == 1
                revisions_mock.append.assert_called_with(new_rev)

                assert mocked_store.call_count == 1
                mocked_store.assert_called_with(mocked_request.registry.db)

                assert mocked_logger.info.call_count == 1
                mocked_logger.info.assert_called_with(
                    'Saved lot {lot_id}: dateModified {old_dateModified} -> {new_dateModified}'.format(
                        lot_id=lot.id,
                        old_dateModified=old_date.isoformat(),
                        new_dateModified=new_date.isoformat()),
                    extra=unpacked_context
                )

                # Check ModelValidationError
                lot.dateModified = old_date

                mocked_get_now.side_effect = iter([
                    new_date
                ])
                mocked_lot_revisions.model_class.side_effect = iter([new_rev])
                mocked_prepare_revision.side_effect = iter([rev_data])

                error_key = 'error'
                error_message = 'Some error'
                mocked_store.side_effect = iter([
                    ModelValidationError({error_key: error_message})
                ])
                assert store_lot(lot, patch, mocked_request) is None

                mocked_prepare_revision.assert_called_with(
                    lot,
                    patch,
                    mocked_request.authenticated_userid
                )

                assert mocked_lot_revisions.model_class.call_count == 2
                mocked_lot_revisions.model_class.assert_called_with(rev_data)

                assert revisions_mock.append.call_count == 2
                revisions_mock.append.assert_called_with(new_rev)

                assert mocked_store.call_count == 2
                mocked_store.assert_called_with(mocked_request.registry.db)

                assert mocked_request.errors.add.call_count == 1
                assert mocked_request.errors.status == 422
                mocked_request.errors.add.assert_called_with('body', error_key, error_message)

                mocked_request.errors.status = None

                # Check ResourceConflict
                lot.dateModified = old_date

                mocked_get_now.side_effect = iter([
                    new_date
                ])
                mocked_lot_revisions.model_class.side_effect = iter([new_rev])
                mocked_prepare_revision.side_effect = iter([rev_data])

                error_message = 'conflict error'
                mocked_store.side_effect = iter([
                    ResourceConflict(error_message)
                ])
                assert store_lot(lot, patch, mocked_request) is None

                mocked_prepare_revision.assert_called_with(
                    lot,
                    patch,
                    mocked_request.authenticated_userid
                )

                assert mocked_lot_revisions.model_class.call_count == 3
                mocked_lot_revisions.model_class.assert_called_with(rev_data)

                assert revisions_mock.append.call_count == 3
                revisions_mock.append.assert_called_with(new_rev)

                assert mocked_store.call_count == 3
                mocked_store.assert_called_with(mocked_request.registry.db)

                assert mocked_request.errors.add.call_count == 2
                assert mocked_request.errors.status == 409
                mocked_request.errors.add.assert_called_with('body', 'data', error_message)

                mocked_request.errors.status = None

                # Check Exception
                lot.dateModified = old_date

                mocked_get_now.side_effect = iter([
                    new_date
                ])
                mocked_lot_revisions.model_class.side_effect = iter([new_rev])
                mocked_prepare_revision.side_effect = iter([rev_data])

                error_message = 'just exception'
                mocked_store.side_effect = iter([
                    Exception(error_message)
                ])
                assert store_lot(lot, patch, mocked_request) is None

                mocked_prepare_revision.assert_called_with(
                    lot,
                    patch,
                    mocked_request.authenticated_userid
                )

                assert mocked_lot_revisions.model_class.call_count == 4
                mocked_lot_revisions.model_class.assert_called_with(rev_data)

                assert revisions_mock.append.call_count == 4
                revisions_mock.append.assert_called_with(new_rev)

                assert mocked_store.call_count == 4
                mocked_store.assert_called_with(mocked_request.registry.db)

                assert mocked_request.errors.add.call_count == 3
                assert mocked_request.errors.status is None
                mocked_request.errors.add.assert_called_with('body', 'data', error_message)

                # Check modified is False
                lot.modified = False
                lot.dateModified = old_date

                mocked_context_unpack.side_effect = iter([
                    unpacked_context
                ])
                mocked_get_now.side_effect = iter([
                    new_date
                ])
                mocked_store.side_effect = iter([
                    None
                ])
                mocked_lot_revisions.model_class.side_effect = iter([new_rev])
                mocked_prepare_revision.side_effect = iter([rev_data])


                assert store_lot(lot, patch, mocked_request) is True

                assert mocked_prepare_revision.call_count == 5
                mocked_prepare_revision.assert_called_with(
                    lot,
                    patch,
                    mocked_request.authenticated_userid
                )

                assert mocked_lot_revisions.model_class.call_count == 5
                mocked_lot_revisions.model_class.assert_called_with(rev_data)

                assert revisions_mock.append.call_count == 5
                revisions_mock.append.assert_called_with(new_rev)

                assert mocked_store.call_count == 5
                mocked_store.assert_called_with(mocked_request.registry.db)

                assert mocked_logger.info.call_count == 2
                mocked_logger.info.assert_called_with(
                    'Saved lot {lot_id}: dateModified {old_dateModified} -> {new_dateModified}'.format(
                        lot_id=lot.id,
                        old_dateModified=old_date.isoformat(),
                        new_dateModified=old_date.isoformat()),
                    extra=unpacked_context
                )
