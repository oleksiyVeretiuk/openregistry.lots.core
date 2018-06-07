# -*- coding: utf-8 -*-
from openprocurement.api.plugins.transferring.validation import (
    validate_ownership_data
)

from openregistry.lots.core.plugins.transferring.validation import (
    validate_lot_accreditation_level
)
from openregistry.lots.core.constants import (
    ROUTE_PREFIX
)
from openregistry.lots.core.utils import (
    oplotsresource,
    json_view,
    context_unpack,
    APIResource,
    save_lot
)


@oplotsresource(name='Lot ownership',
                path='/lots/{lot_id}/ownership',
                description="Lots Ownership")
class AuctionsResource(APIResource):

    @json_view(permission='create_lot',
               validators=(validate_lot_accreditation_level,
                           validate_ownership_data))
    def post(self):
        lot = self.request.validated['lot']
        location = self.request.route_path('Lot', lot_id=lot.id)
        location = location[len(ROUTE_PREFIX):]  # strips /api/<version>
        ownership_changed = self.request.change_ownership(location)

        if ownership_changed and save_lot(self.request):
            self.LOGGER.info(
                'Updated ownership of lot {}'.format(lot.id),
                extra=context_unpack(
                    self.request, {'MESSAGE_ID': 'auction_ownership_update'}
                )
            )

            return {'data': self.request.context.serialize('view')}


@oplotsresource(
    name='Auction credentials',
    path='/lots/{lot_id}/extract_credentials',
    description="Auctions Extract Credentials"
)
class AuctionResource(APIResource):

    @json_view(permission='extract_credentials')
    def get(self):
        self.LOGGER.info('Extract credentials for lot {}'.format(self.context.id))
        lot = self.request.validated['lot']
        data = lot.serialize('extract_credentials') or {}
        data['transfer_token'] = lot.transfer_token
        return {'data': data}
