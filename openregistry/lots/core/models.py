# -*- coding: utf-8 -*-
from schematics.transforms import whitelist, blacklist
from schematics.types import BaseType, StringType, MD5Type
from schematics.types.compound import ModelType, DictType, ListType
from schematics.exceptions import ValidationError
from couchdb_schematics.document import SchematicsDocument
from zope.interface import implementer
from schematics.types.serializable import serializable
from pyramid.security import Allow

from openregistry.api.models.ocds import (
    Revision,
    Organization
)
from openregistry.api.models.schematics_extender import (
    Model, IsoDateTimeType,
)
from openregistry.api.models.roles import (
    schematics_embedded_role,
    schematics_default_role,
    plain_role, listing_role,
)

from openregistry.api.interfaces import IORContent


create_role = (blacklist('owner_token', 'owner', '_attachments', 'revisions',
                         'date', 'dateModified', 'lotID',
                         'status', 'doc_id') + schematics_embedded_role)
edit_role = (blacklist('owner_token', 'owner', 'status', '_attachments',
                       'revisions', 'date', 'dateModified',
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
class BaseLot(SchematicsDocument, Model):
    class Options:
        roles = {
            'create': create_role,
            'draft': view_role,
            'plain': plain_role,
            'edit': edit_role,
            'waiting': view_role,
            'edit_waiting': edit_role,
            'active.pending': view_role,
            'edit_active.pending': blacklist('revisions'),
            'edit_active.inauction': edit_role,
            'pending': view_role,
            'view': view_role,
            'listing': listing_role,
            'Administrator': Administrator_role,
            'default': schematics_default_role,
        }

    lotID = StringType()  # lotID should always be the same as the OCID. It is included to make the flattened data structure more convenient.
    mode = StringType(choices=['test'])
    owner = StringType()
    owner_token = StringType()
    date = IsoDateTimeType()
    dateModified = IsoDateTimeType()
    title = StringType(required=True)
    title_en = StringType()
    title_ru = StringType()
    description = StringType()
    description_en = StringType()
    description_ru = StringType()
    lotCustodian = ModelType(Organization, required=True)

    _attachments = DictType(DictType(BaseType), default=dict())  # couchdb attachments
    revisions = ListType(ModelType(Revision), default=list())

    create_accreditation = 1
    edit_accreditation = 2

    __name__ = ''

    def __repr__(self):
        return '<%s:%r@%r>' % (type(self).__name__, self.id, self.rev)

    def __local_roles__(self):
        roles = dict([('{}_{}'.format(self.owner, self.owner_token), 'lot_owner')])
        return roles

    @serializable(serialized_name='id')
    def doc_id(self):
        """A property that is serialized by schematics exports."""
        return self._id

    def get_role(self):
        root = self.__parent__
        request = root.request
        if request.authenticated_role == 'Administrator':
            role = 'Administrator'
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
    status = StringType(choices=['draft', 'waiting', 'active.pending',
                                 'active.inauction', 'sold', 'dissolved',
                                 'deleted', 'invalid'],
                        default='waiting')
    auctions = ListType(MD5Type(), default=list())
    assets = ListType(MD5Type(), required=False, validators=[
        validate_asset_uniq,
    ])

    create_accreditation = 1
    edit_accreditation = 2
