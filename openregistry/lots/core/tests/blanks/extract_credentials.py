from openregistry.lots.core.utils import get_forbidden_users

def get_extract_credentials(self):
    expected_keys = ('owner', 'transfer_token')
    self.app.authorization = ('Basic', (self.valid_user, ''))
    path = '/{}/extract_credentials'.format(self.resource_id)
    response = self.app.get(path)
    response_data_keys = response.json['data'].keys()
    self.assertSetEqual(set(expected_keys), set(response_data_keys))


def forbidden_users(self):
    forbidden_users = get_forbidden_users(allowed_levels=('3'))
    for user in forbidden_users:
        self.app.authorization = ('Basic', (user, ''))
        self.app.get('/{}/extract_credentials'.format(self.resource_id), status=403)
