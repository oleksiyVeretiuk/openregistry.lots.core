# -*- coding: utf-8 -*-
from pyramid.security import Allow
from schematics.exceptions import ValidationError
from schematics.transforms import whitelist, blacklist
from schematics.types import StringType, MD5Type
from schematics.types.compound import ModelType, ListType
from zope.interface import implementer

from openprocurement.api.constants import (  # noqa: F401
    IDENTIFIER_CODES,  # noqa forwarded import
    SANDBOX_MODE
)
from openprocurement.api.interfaces import IORContent
from openprocurement.api.models.auction_models import Value  # noqa forwarded import
from openprocurement.api.models.schema import (  # noqa: forwarded  import
    RelatedProcess,
)
from openprocurement.api.models.common import (  # noqa: F401
    sensitive_embedded_role,
    BaseResourceItem,
    Guarantee,  # noqa forwarded import
    Period,  # noqa forwarded import
    Classification,  # noqa forwarded import
    BaseUnit,  # noqa forwarded import
    Address,  # noqa forwarded import
    ContactPoint,  # noqa forwarded import
    BankAccount,  # noqa forwarded import
    AuctionParameters,  # noqa forwarded import
)
from openprocurement.api.models.ocds import (  # noqa: F401
    Identifier as BaseIdentifier,  # noqa forwarded import
    Document,  # noqa forwarded import
    Item,  # noqa forwarded import
    Organization,
    ItemClassification,  # noqa forwarded import
)
from openprocurement.api.models.registry_models import (  # noqa: F401
    LokiDocument,  # noqa forwarded import
    LokiItem,  # noqa forwarded import
    Decision,  # noqa forwarded import
    AssetCustodian,  # noqa forwarded import
    AssetHolder  # noqa forwarded import
)
from openprocurement.api.models.roles import (  # noqa: F401
    schematics_embedded_role, # noqa forwarded import
    schematics_default_role,
    plain_role,
    listing_role
)
from openprocurement.api.models.schematics_extender import (  # noqa: F401
    Model,  # noqa forwarded import
    IsoDateTimeType,
    IsoDurationType,  # noqa forwarded import
    DecimalType  # noqa forwarded import
)

from .constants import LOT_STATUSES

lots_embedded_role = sensitive_embedded_role

create_role = (blacklist('owner', '_attachments', 'revisions',
                         'date', 'dateModified', 'lotID', 'documents',
                         'status', 'doc_id') + lots_embedded_role)
edit_role = (blacklist('owner', '_attachments', 'lotType',
                       'revisions', 'date', 'dateModified', 'documents',
                       'lotID', 'mode', 'doc_id') + lots_embedded_role)
view_role = (blacklist('_attachments', 'revisions') + lots_embedded_role)

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
            # Pending.deleted role
            'pending.deleted': view_role,
            'edit_pending.deleted': whitelist(),
            # Deleted role
            'deleted': view_role,
            'edit_deleted': whitelist(),
            # Verification role
            'verification': view_role,
            'edit_verification': whitelist(),
            # Recomposed role
            'recomposed': view_role,
            'edit_recomposed': whitelist(),
            # Active.salable role
            'active.salable':  view_role,
            'edit_active.salable': whitelist('status'),
            # pending.dissolution role
            'pending.dissolution': view_role,
            'edit_pending.dissolution': whitelist('status'),
            # Dissolved role
            'dissolved': view_role,
            'edit_dissolved': whitelist(),
            # Active.awaiting role
            'active.awaiting': view_role,
            'edit_active.awaiting': whitelist(),
            # Active.auction role
            'active.auction': view_role,
            'edit_active.auction': edit_role,
            # pending.sold role
            'pending.sold': view_role,
            'edit.pending.sold': whitelist(),
            # Sold role
            'sold': view_role,
            'concierge': whitelist('status'),
            'convoy': whitelist('status', 'auctions'),
            'extract_credentials': whitelist('owner', 'id')
        }

    # lotID should always be the same as the OCID. It is included to make the flattened data structure more convenient.
    lotID = StringType()
    date = IsoDateTimeType()
    title = StringType(required=True)
    title_en = StringType()
    title_ru = StringType()
    description = StringType()
    description_en = StringType()
    description_ru = StringType()
    lotCustodian = ModelType(Organization, required=True)
    documents = ListType(ModelType(Document), default=list())  # All documents and attachments related to the lot.

    _internal_type = None

    if SANDBOX_MODE:
        sandboxParameters = StringType()

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

    def validate_sandboxParameters(self, *args, **kw):
        if self.mode and self.mode == 'test' and self.sandboxParameters and self.sandboxParameters != '':
            raise ValidationError(u"procurementMethodDetails should be used with mode test")


def validate_asset_uniq(assets, *args):
    if len(assets) != len(set(assets)):
        raise ValidationError(u"Assets should be unique")


class Lot(BaseLot):
    status = StringType(choices=LOT_STATUSES,
                        default='draft')
    auctions = ListType(MD5Type(), default=list())

    def __init__(self, *args, **kwargs):
        super(Lot, self).__init__(*args, **kwargs)
        self.doc_type = "Lot"
