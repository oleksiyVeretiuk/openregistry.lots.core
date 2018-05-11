# -*- coding: utf-8 -*-
import unittest
import mock

from couchdb.http import ResourceConflict
from datetime import datetime


from openregistry.lots.core.utils import get_now
from openregistry.lots.core.utils import (
    generate_lot_id,
    extract_lot,
    extract_lot_adapter,
    lot_from_data,
    register_lotType,
    apply_patch

)
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
        db.get.side_effect = [{}]
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
        db.get.side_effect = [{}]
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
        db.get.side_effect = [{mocked_key: index}]
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
        db.get.side_effect = [{}, {}, {}]
        db.save.side_effect = [DummyException, ResourceConflict, None]
        generate_lot_id(ctime, db)
        assert db.get.call_count == 6
        assert db.save.call_count == 6

    @mock.patch('openregistry.lots.core.utils.decode_path_info')
    @mock.patch('openregistry.lots.core.utils.extract_lot_adapter')
    def test_extract_lot(self, mocked_extract_lot_adapter, mocked_decode_path_info):
        mocked_request = mock.MagicMock()
        mocked_request.environ = {}

        # Check with KeyError
        mocked_extract_lot_adapter.side_effect = ['adapter']
        returned_value = extract_lot(mocked_request)
        assert returned_value is None
        assert mocked_extract_lot_adapter.call_count == 0
        assert mocked_decode_path_info.call_count == 0

        # Check with path with id
        path = 'domain/api/0/lots/lotID'
        mocked_extract_lot_adapter.side_effect = ['adapter']
        mocked_request.environ = {'PATH_INFO': path}
        mocked_decode_path_info.side_effect = [path]

        returned_value = extract_lot(mocked_request)

        assert returned_value == 'adapter'
        assert mocked_decode_path_info.call_count == 1
        assert mocked_extract_lot_adapter.call_count == 1
        mocked_extract_lot_adapter.assert_called_with(mocked_request, path.split('/')[4])


        # Check with path without len less 4
        path = 'domain/api/0/'
        mocked_extract_lot_adapter.side_effect = ['adapter']
        mocked_request.environ = {'PATH_INFO': path}
        mocked_decode_path_info.side_effect = [path]

        returned_value = extract_lot(mocked_request)
        assert returned_value is None
        assert mocked_decode_path_info.call_count == 2
        assert mocked_extract_lot_adapter.call_count == 1

        # Check with path without lots in path
        path = 'domain/api/0/notLots'
        mocked_extract_lot_adapter.side_effect = ['adapter']
        mocked_request.environ = {'PATH_INFO': path}
        mocked_decode_path_info.side_effect = [path]

        returned_value = extract_lot(mocked_request)
        assert returned_value is None
        assert mocked_decode_path_info.call_count == 3
        assert mocked_extract_lot_adapter.call_count == 1

    @mock.patch('openregistry.lots.core.utils.error_handler')
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
        db.get.side_effect = [doc]
        mocked_handler.side_effect = [DummyException]

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
        db.get.side_effect = [doc]
        mocked_handler.side_effect = [DummyException]

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
        db.get.side_effect = [doc]
        mocked_request.lot_from_data.side_effect = ['lotFromData']
        returned_value = extract_lot_adapter(mocked_request, lot_id)
        assert returned_value == 'lotFromData'
        assert db.get.call_count == 3
        db.get.assert_called_with(lot_id)

        assert mocked_request.errors.add.call_count == 2
        assert mocked_request.errors.status is None
        assert mocked_handler.call_count == 2

        assert mocked_request.lot_from_data.call_count == 1
        mocked_request.lot_from_data.assert_called_with(doc)


    @mock.patch('openregistry.lots.core.utils.update_logging_context')
    @mock.patch('openregistry.lots.core.utils.error_handler')
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
        mocked_model.side_effect = ['model']
        mocked_handler.side_effect = [DummyException]
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
        mocked_model.side_effect = ['model']
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
        mocked_model.side_effect = ['model']
        mocked_handler.side_effect = [DummyException]

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
        mocked_model.side_effect = ['model']
        mocked_handler.side_effect = [DummyException]

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

    @mock.patch('openregistry.lots.core.utils.save_lot')
    @mock.patch('openregistry.lots.core.utils.apply_data_patch')
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
        mocked_apply_data.side_effect = [patch]
        context.serialize.side_effect = [serialized_data]
        mocked_save_lot.side_effect = [saved_lot]

        returned_value = apply_patch(mocked_request)
        assert returned_value == saved_lot

        assert mocked_apply_data.call_count == 1
        mocked_apply_data.assert_called_with(serialized_data, mocked_request.validated['data'])

        assert context.import_data.call_count == 1
        context.import_data.assert_called_with(patch)

        assert mocked_save_lot.call_count == 1
        mocked_save_lot.assert_called_with(mocked_request)

        # Check apply_patch if data is not None
        mocked_request.validated = {}
        data = 'someData'
        mocked_apply_data.side_effect = [patch]
        context.serialize.side_effect = [serialized_data]
        mocked_save_lot.side_effect = [saved_lot]

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
        mocked_apply_data.side_effect = [patch]
        context.serialize.side_effect = [serialized_data]
        mocked_save_lot.side_effect = [saved_lot]

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
        mocked_apply_data.side_effect = [patch]
        context.serialize.side_effect = [serialized_data]
        mocked_save_lot.side_effect = [saved_lot]

        returned_value = apply_patch(mocked_request, save=False)
        assert returned_value is None

        assert mocked_apply_data.call_count == 4
        mocked_apply_data.assert_called_with(serialized_data, mocked_request.validated['data'])

        assert context.import_data.call_count == 4
        context.import_data.assert_called_with(patch)

        assert mocked_save_lot.call_count == 3

        # Check apply_patch if all data is None
        mocked_request.validated['data'] = None
        mocked_apply_data.side_effect = [patch]
        context.serialize.side_effect = [serialized_data]
        mocked_save_lot.side_effect = [saved_lot]

        returned_value = apply_patch(mocked_request)
        assert returned_value is None

        assert mocked_apply_data.call_count == 4

        assert context.import_data.call_count == 4
        context.import_data.assert_called_with(patch)

        assert mocked_save_lot.call_count == 3

        # Check apply_patch if apply_data_patch return None
        mocked_request.validated['data'] = 'data'
        mocked_apply_data.side_effect = [None]
        context.serialize.side_effect = [serialized_data]
        mocked_save_lot.side_effect = [saved_lot]

        returned_value = apply_patch(mocked_request, save=False)
        assert returned_value is None

        assert mocked_apply_data.call_count == 5
        mocked_apply_data.assert_called_with(serialized_data, mocked_request.validated['data'])

        assert context.import_data.call_count == 4
        context.import_data.assert_called_with(patch)

        assert mocked_save_lot.call_count == 3







