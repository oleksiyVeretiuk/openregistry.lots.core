# -*- coding: utf-8 -*-
from openprocurement.api.validation import validate_data, validate_json_data
from .utils import update_logging_context, raise_operation_error
from openprocurement.api.validation import (
    validate_file_upload,  # noqa forwarded import
    validate_document_data,  # noqa forwarded import
    validate_change_status,  # noqa forwarded import
    validate_patch_document_data,  # noqa forwarded import
)

def validate_lot_data(request, error_handler, **kwargs):
    update_logging_context(request, {'lot_id': '__new__'})

    data = validate_json_data(request)
    model = request.lot_from_data(data, create=False)
    if not any([request.check_accreditation(acc) for acc in iter(str(model.create_accreditation))]):
        request.errors.add('body', 'accreditation',
                           'Broker Accreditation level does not permit lot creation')
        request.errors.status = 403
        raise error_handler(request.errors)

    data = validate_data(request, model, data=data)
    if data and data.get('mode', None) is None and request.check_accreditation('t'):
        request.errors.add('body', 'mode', 'Broker Accreditation level does not permit lot creation')
        request.errors.status = 403
        raise error_handler(request)


def validate_post_lot_role(request, error_handler, **kwargs):
    if request.authenticated_role in ('convoy', 'concierge'):
        request.errors.add('body', 'accreditation', 'Can\'t create lot as bot')
        request.errors.status = 403
        raise error_handler(request)


def validate_patch_lot_data(request, error_handler, **kwargs):
    data = validate_json_data(request)
    editing_roles = request.content_configurator.available_statuses[request.context.status]['editing_permissions']
    if request.authenticated_role not in editing_roles:
        msg = 'Can\'t update {} in current ({}) status'.format(request.validated['resource_type'],
                                                               request.context.status)
        raise_operation_error(request, error_handler, msg)
    default_status = type(request.lot).fields['status'].default
    if data.get('status') == default_status and data.get('status') != request.context.status:
        raise_operation_error(request, error_handler, 'Can\'t switch lot to {} status'.format(default_status))
    return validate_data(request, type(request.lot), True, data)


def validate_lot_document_update_not_by_author_or_lot_owner(request, error_handler, **kwargs):
    if request.authenticated_role != (request.context.author or 'lot_owner'):
        request.errors.add('url', 'role', 'Can update document only author')
        request.errors.status = 403
        raise error_handler(request)
