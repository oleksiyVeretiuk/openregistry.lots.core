# -*- coding: utf-8 -*-
from openregistry.assets.core.events import AssetInitializeEvent
from openregistry.assets.core.design import (
    FIELDS, VIEW_MAP, CHANGES_VIEW_MAP, FEED
)

from openregistry.api.utils import (
    get_now, decrypt, encrypt, generate_id, json_view, set_ownership,
    context_unpack, APIResourceListing
)

from openregistry.assets.core.utils import (
    save_asset, asset_serialize, opassetsresource, generate_asset_id
)

from openregistry.assets.core.validation import (
    validate_asset_data,
)


@opassetsresource(name='Assets',
                  path='/assets',
                  description="Open Contracting compatible data exchange format.")
class AssetsResource(APIResourceListing):

    def __init__(self, request, context):
        super(AssetsResource, self).__init__(request, context)
        # params for listing
        self.VIEW_MAP = VIEW_MAP
        self.CHANGES_VIEW_MAP = CHANGES_VIEW_MAP
        self.FEED = FEED
        self.FIELDS = FIELDS
        self.serialize_func = asset_serialize
        self.object_name_for_listing = 'Assets'
        self.log_message_id = 'asset_list_custom'

    @json_view(content_type="application/json", permission='create_asset', validators=(validate_asset_data,))
    def post(self):
        """This API request is targeted to creating new Asset."""

        asset_id = generate_id()
        asset = self.request.validated['asset']
        asset.id = asset_id
        if not asset.get('assetID'):
            asset.assetID = generate_asset_id(get_now(), self.db, self.server_id)
        self.request.registry.notify(AssetInitializeEvent(asset))
        if self.request.json_body['data'].get('status') == 'draft':
            asset.status = 'draft'
        set_ownership(asset, self.request)  # rewrite as subscriber?
        self.request.validated['asset'] = asset
        self.request.validated['asset_src'] = {}
        if save_asset(self.request):
            self.LOGGER.info('Created asset {} ({})'.format(asset_id, asset.assetID),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'asset_create'}, {'asset_id': asset_id, 'assetID': asset.assetID}))
            self.request.response.status = 201
            self.request.response.headers[
                'Location'] = self.request.route_url('{}:Asset'.format(asset.assetType), asset_id=asset_id)
            return {
                'data': asset.serialize(asset.status),
                'access': {
                    'token': asset.owner_token
                }
            }
