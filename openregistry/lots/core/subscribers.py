# -*- coding: utf-8 -*-
from pyramid.events import subscriber
from pyramid.events import ContextFound
from openregistry.api.events import ErrorDesctiptorEvent
from openregistry.api.utils import update_logging_context


@subscriber(ErrorDesctiptorEvent)
def tender_error_handler(event):
    if 'lot' in event.request.validated:
        event.params['LOT_REV'] = event.request.validated['lot'].rev
        event.params['LOTID'] = event.request.validated['lot'].lotID
        event.params['LOT_STATUS'] = event.request.validated['lot'].status


@subscriber(ContextFound)
def extend_lot_logging_context(event):
    request = event.request
    if 'lot' in request.validated:
        params = dict()
        params['LOT_REV'] = request.validated['lot'].rev
        params['LOTID'] = request.validated['lot'].lotID
        params['LOT_STATUS'] = request.validated['lot'].status
        update_logging_context(request, params)
