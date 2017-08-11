# -*- coding: utf-8 -*-

from pyramid.security import (
    ALL_PERMISSIONS,
    Allow,
    Deny,
    Everyone,
)
from openregistry.api.traversal import get_item


class Root(object):
    __name__ = None
    __parent__ = None
    __acl__ = [
        # (Allow, Everyone, ALL_PERMISSIONS),
        (Allow, Everyone, 'view_listing'),
        (Allow, Everyone, 'view_lot'),
        (Allow, 'g:brokers', 'create_lot'),
        (Allow, 'g:brokers', 'edit_lot'),
        (Allow, 'g:Administrator', 'edit_lot'),
        (Allow, 'g:admins', ALL_PERMISSIONS),
        (Allow, 'g:bot1', 'edit_lot'),
        (Allow, 'g:bot2', 'edit_lot'),
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
    if request.method != 'GET':
        request.validated['lot_src'] = lot.serialize('plain')
    if request.matchdict.get('document_id'):
        return get_item(lot, 'document', request)
    request.validated['id'] = request.matchdict['lot_id']
    return lot
