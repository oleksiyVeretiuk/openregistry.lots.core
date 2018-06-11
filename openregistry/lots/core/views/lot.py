# -*- coding: utf-8 -*-
from openregistry.lots.core.utils import (
    json_view,
    context_unpack,
    APIResource
)
from openregistry.lots.core.interfaces import ILotManager

from openregistry.lots.core.utils import (
    oplotsresource, apply_patch
)

from openregistry.lots.core.validation import (
    validate_patch_lot_data,
)


patch_lot_validators = (
    validate_patch_lot_data,
)


@oplotsresource(name='Lot',
                path='/lots/{lot_id}',
                description="Open Contracting compatible data exchange format.")
class LotResource(APIResource):

    @json_view(permission='view_lot')
    def get(self):
        lot_data = self.context.serialize(self.context.status)
        return {'data': lot_data}

    @json_view(content_type="application/json", validators=patch_lot_validators,
               permission='edit_lot')
    def patch(self):
        self.request.registry.getAdapter(self.context, ILotManager).change_lot(self.request)
        lot = self.context
        apply_patch(self.request, src=self.request.validated['lot_src'])
        self.LOGGER.info(
            'Updated lot {}'.format(lot.id),
            extra=context_unpack(self.request, {'MESSAGE_ID': 'lot_patch'})
        )
        return {'data': lot.serialize(lot.status)}
