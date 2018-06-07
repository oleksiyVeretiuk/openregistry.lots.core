# -*- coding: utf-8 -*-
from openprocurement.api.plugins.transferring.validation import validate_accreditation_level


def validate_lot_accreditation_level(request, **kwargs):  # pylint: disable=unused-argument
    if hasattr(request.validated['lot'], 'transfer_accreditation'):
        predicate = 'transfer_accreditation'
    else:
        predicate = 'create_accreditation'
    validate_accreditation_level(request, request.validated['lot'], predicate)
