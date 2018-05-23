from logging import getLogger
from functools import partial
from time import sleep
from pkg_resources import get_distribution
from couchdb.http import ResourceConflict
from schematics.exceptions import ModelValidationError
from cornice.resource import resource
from pyramid.compat import decode_path_info
from pyramid.exceptions import URLDecodeError


from openprocurement.api.utils import (  # noqa: F401
    get_file,  # noqa forwarded import
    calculate_business_date,  # noqa forwarded import
    update_file_content_type,  # noqa forwarded import
    json_view,  # noqa forwarded import
    context_unpack,
    APIResource,  # noqa forwarded import
    error_handler,
    set_modetest_titles,
    get_revision_changes,
    get_now,
    apply_data_patch,
    prepare_revision,
    raise_operation_error,  # noqa forwarded import
    update_logging_context
)

from openregistry.lots.core.constants import DEFAULT_LOT_TYPE

from openregistry.lots.core.traversal import factory

PKG = get_distribution(__package__)
LOGGER = getLogger(PKG.project_name)


oplotsresource = partial(resource,
                         error_handler=error_handler,
                         factory=factory)


def generate_lot_id(ctime, db, server_id=''):
    key = ctime.date().isoformat()
    lotIDdoc = 'lotID_' + server_id if server_id else 'lotID'
    while True:
        try:
            lotID = db.get(lotIDdoc, {'_id': lotIDdoc})
            index = lotID.get(key, 1)
            lotID[key] = index + 1
            db.save(lotID)
        except ResourceConflict:  # pragma: no cover
            pass
        except Exception:  # pragma: no cover
            sleep(1)
        else:
            break
    return 'UA-LR-DGF-{:04}-{:02}-{:02}-{:06}{}'.format(
                                                ctime.year,
                                                ctime.month,
                                                ctime.day,
                                                index,
                                                server_id and '-' + server_id
                                            )


def extract_lot(request):
    try:
        # empty if mounted under a path in mod_wsgi, for example
        path = decode_path_info(request.environ['PATH_INFO'] or '/')
    except KeyError:
        path = '/'
    except UnicodeDecodeError as e:
        raise URLDecodeError(e.encoding, e.object, e.start, e.end, e.reason)

    lot_id = ""
    # extract lot id
    parts = path.split('/')
    if len(parts) < 4 or parts[3] != 'lots':
        return

    lot_id = parts[4]
    return extract_lot_adapter(request, lot_id)


def extract_lot_adapter(request, lot_id):
    db = request.registry.db
    doc = db.get(lot_id)
    if doc is None or doc.get('doc_type') != 'Lot':
        request.errors.add('url', 'lot_id', 'Not Found')
        request.errors.status = 404
        raise error_handler(request)

    return request.lot_from_data(doc)


def get_lot_types(registry, internal_types):
    lot_types = [
        lt for lt, it in registry.lot_type_configurator.items() if it in internal_types
    ]
    return lot_types


def lot_from_data(request, data, raise_error=True, create=True):
    lotType = data.get('lotType')
    if not lotType:
        lot_types = get_lot_types(request.registry, (DEFAULT_LOT_TYPE,))
        lotType = lot_types[0] if lot_types else DEFAULT_LOT_TYPE
    model = request.registry.lotTypes.get(lotType)
    if model is None and raise_error:
        request.errors.add('body', 'lotType', 'Not implemented')
        request.errors.status = 415
        raise error_handler(request)
    update_logging_context(request, {'lot_type': lotType})
    if model is not None and create:
        model = model(data)
    return model


def apply_patch(request, data=None, save=True, src=None):
    data = request.validated.get('data') if data is None else data
    patch = data and apply_data_patch(src or request.context.serialize(), data)
    if patch:
        request.context.import_data(patch)
        if save:
            return save_lot(request)


class isLot(object):
    """ Route predicate. """

    def __init__(self, val, config):
        self.val = val

    def text(self):
        return 'lotType = %s' % (self.val,)

    phash = text

    def __call__(self, context, request):
        if request.lot is not None:
            lot_type = getattr(request.lot, 'lotType', None)
            return request.registry.lot_type_configurator.get(lot_type) == self.val
        return False


def register_lotType(config, model, lot_type):
    """Register a lotType.
    :param config:
        The pyramid configuration object that will be populated.
    :param model:
        The lot model class
    """
    config.registry.lotTypes[lot_type] = model
    config.registry.lot_type_configurator[lot_type] = model._internal_type


class SubscribersPicker(isLot):
    """ Subscriber predicate. """

    def __call__(self, event):
        if event.lot is not None:
            return getattr(event.lot, 'lotType', None) == self.val
        return False


def lot_serialize(request, lot_data, fields):
    lot = request.lot_from_data(lot_data, raise_error=False)
    if lot is None:
        return dict([(i, lot_data.get(i, '')) for i in ['lotType', 'dateModified', 'id']])
    return dict([(i, j) for i, j in lot.serialize(lot.status).items() if i in fields])


def store_lot(lot, patch, request):
    revision = prepare_revision(lot, patch, request.authenticated_userid)
    lot.revisions.append(type(lot).revisions.model_class(revision))
    old_dateModified = lot.dateModified
    if getattr(lot, 'modified', True):
        lot.dateModified = get_now()
    try:
        lot.store(request.registry.db)
    except ModelValidationError, e:
        for i in e.message:
            request.errors.add('body', i, e.message[i])
        request.errors.status = 422
    except ResourceConflict, e:  # pragma: no cover
        request.errors.add('body', 'data', str(e))
        request.errors.status = 409
    except Exception, e:  # pragma: no cover
        request.errors.add('body', 'data', str(e))
    else:
        LOGGER.info(
            'Saved lot {lot_id}: dateModified {old_dateModified} -> {new_dateModified}'.format(
                lot_id=lot.id,
                old_dateModified=old_dateModified and old_dateModified.isoformat(),
                new_dateModified=lot.dateModified.isoformat()),
            extra=context_unpack(request, {'MESSAGE_ID': 'save_lot'}, {'RESULT': lot.rev}))
        return True


def save_lot(request):
    lot = request.validated['lot']
    if lot.mode == u'test':
        set_modetest_titles(lot)
    patch = get_revision_changes(lot.serialize("plain"), request.validated['lot_src'])
    if patch:
        return store_lot(lot, patch, request)
