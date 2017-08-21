# -*- coding: utf-8 -*-
from schematics.transforms import whitelist, blacklist
from schematics.types import BaseType, StringType, MD5Type
from schematics.types.compound import ModelType, DictType, ListType
from schematics.exceptions import ValidationError
from zope.interface import implementer
from pyramid.security import Allow

from openregistry.api.models.ocds import Organization, Document
from openregistry.api.models.schematics_extender import IsoDateTimeType
from openregistry.api.models.common import BaseResourceItem
from openregistry.api.models.roles import (
    schematics_embedded_role,
    schematics_default_role,
    plain_role, listing_role,
)

from openregistry.api.interfaces import IORContent
from .constants import LOT_STATUSES


create_role = (blacklist('owner_token', 'owner', '_attachments', 'revisions',
                         'date', 'dateModified', 'lotID', 'documents',
                         'status', 'doc_id') + schematics_embedded_role)
edit_role = (blacklist('owner_token', 'owner', '_attachments',
                       'revisions', 'date', 'dateModified', 'documents',
                       'lotID', 'mode', 'doc_id') + schematics_embedded_role)
view_role = (blacklist('owner_token',
                       '_attachments', 'revisions') + schematics_embedded_role)

Administrator_role = whitelist('status', 'mode')


class ILot(IORContent):
    """ Base lot marker interface """


def get_lot(model):
    while not ILot.providedBy(model):
        model = model.__parent__
    return model


@implementer(ILot)
class BaseLot(BaseResourceItem):
    class Options:
        roles = {
            'create': create_role,
            'plain': plain_role,
            'edit': edit_role,
            'view': view_role,
            'listing': listing_role,
            'default': schematics_default_role,
            'Administrator': Administrator_role,
            # Draft role
            'draft': view_role,
            'edit_draft': whitelist('status'),
            # Pending role
            'pending': view_role,
            'edit_pending': edit_role,
            # Deleted role
            'deleted': view_role,
            'edit_deleted': whitelist(),
            # Verification role
            'verification': view_role,
            'edit_verification': whitelist(),
            # Active.salable role
            'active.salable':  view_role,
            'edit_active.salable': whitelist('status'),
            # Dissolved role
            'dissolved': view_role,
            'edit_dissolved': whitelist(),
            # Active.awaiting role
            'active.awaiting': view_role,
            'edit_active.awaiting': whitelist(),
            # Active.auction role
            'active.auction': view_role,
            'edit_active.auction': edit_role,
            # Sold role
            'sold': view_role,
            'concierge': whitelist('status'),
            'convoy': whitelist('status', 'auctions')
        }

    lotID = StringType()  # lotID should always be the same as the OCID. It is included to make the flattened data structure more convenient.
    date = IsoDateTimeType()
    title = StringType(required=True)
    title_en = StringType()
    title_ru = StringType()
    description = StringType()
    description_en = StringType()
    description_ru = StringType()
    lotCustodian = ModelType(Organization, required=True)
    documents = ListType(ModelType(Document), default=list())  # All documents and attachments related to the lot.

    create_accreditation = 1
    edit_accreditation = 2

    def __local_roles__(self):
        roles = dict([('{}_{}'.format(self.owner, self.owner_token), 'lot_owner')])
        return roles

    def get_role(self):
        root = self.__parent__
        request = root.request
        if request.authenticated_role == 'Administrator':
            role = 'Administrator'
        elif request.authenticated_role == 'concierge':
            role = 'concierge'
        elif request.authenticated_role == 'convoy':
            role = 'convoy'
        else:
            role = 'edit_{}'.format(request.context.status)
        return role

    def __acl__(self):
        acl = [
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'edit_lot'),
            (Allow, '{}_{}'.format(self.owner, self.owner_token), 'upload_lot_documents'),
        ]
        return acl


def validate_asset_uniq(assets, *args):
    if len(assets) != len(set(assets)):
        raise ValidationError(u"Assets should be unique")


class Lot(BaseLot):
    status = StringType(choices=LOT_STATUSES,
                        default='draft')
    auctions = ListType(MD5Type(), default=list())
    assets = ListType(MD5Type(), required=False, min_size=1,
                      validators=[validate_asset_uniq])

    create_accreditation = 1
    edit_accreditation = 2
