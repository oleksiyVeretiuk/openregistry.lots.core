# -*- coding: utf-8 -*-
from pyramid.security import (
    Allow,
    Everyone,
)
from openprocurement.api.traversal import get_item


class Root(object):
    __name__ = None
    __parent__ = None
    __acl__ = [
        (Allow, Everyone, 'view_listing'),
        (Allow, Everyone, 'view_lot'),
        (Allow, 'g:brokers', 'create_lot'),
        (Allow, 'g:brokers', 'edit_lot'),
        (Allow, 'g:Administrator', 'edit_lot'),
        (Allow, 'g:convoy', 'edit_lot'),
        (Allow, 'g:caravan', 'edit_lot'),
        (Allow, 'g:chronograph', 'edit_lot'),
        (Allow, 'g:concierge', 'edit_lot'),
        (Allow, 'g:concierge', 'extract_credentials'),
    ]

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db


def factory(request):
    request.validated['lot_src'] = {}
    root = Root(request)
    if not request.matchdict or not request.matchdict.get('lot_id'):
        return root
    request.validated['lot_id'] = request.matchdict['lot_id']
    lot = request.lot
    lot.__parent__ = root
    request.validated['lot'] = request.validated['db_doc'] = lot
    request.validated['lot_status'] = lot.status
    request.validated['resource_type'] = "lot"
    if request.method != 'GET':
        request.validated['lot_src'] = lot.serialize('plain')
    if request.matchdict.get('auction_id'):
        auction = get_item(lot, 'auction', request)
        if request.matchdict.get('document_id'):
            return get_item(auction, 'document', request)
        return auction
    if request.matchdict.get('document_id'):
        return get_item(lot, 'document', request)
    if request.matchdict.get('item_id'):
        return get_item(lot, 'item', request)
    request.validated['id'] = request.matchdict['lot_id']
    return lot
