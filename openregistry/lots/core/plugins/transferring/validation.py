# -*- coding: utf-8 -*-
from openprocurement.api.plugins.transferring.validation import validate_accreditation_level
from openprocurement.api.utils import (
   get_resource_accreditation
)


def validate_lot_accreditation_level(request, **kwargs):  # pylint: disable=unused-argument
    levels = get_resource_accreditation(request, 'lot', request.context, 'create')
    validate_accreditation_level(request, request.validated['lot'], levels)
