# -*- coding: utf-8 -*-


def change_resource_ownership(self):
    change_ownership_url = '{}/{}/ownership'
    post = self.app.post_json

    req_data = {"data": {"id": 1984}}
    response = post(
        change_ownership_url.format(self.resource_name, self.resource_id),
        req_data, status=422
    )
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.json['errors'], [
        {u'description': u'This field is required.',
         u'location': u'body', u'name': u'transfer'}
    ])

    resource = self.get_resource(self.resource_id)
    self.assertEqual(resource['data']['owner'], self.first_owner)

    self.app.authorization = ('Basic', (self.second_owner, ''))

    transfer = self.create_transfer()

    req_data = {"data": {"id": transfer['data']['id'],
                         'transfer': self.resource_transfer}}

    response = post(
        change_ownership_url.format(self.resource_name, self.resource_id),
        req_data
    )
    self.assertEqual(response.status, '200 OK')
    self.assertNotIn('transfer', response.json['data'])
    self.assertNotIn('transfer_token', response.json['data'])
    self.assertEqual(self.second_owner, response.json['data']['owner'])


def resource_location_in_transfer(self):

    used_transfer = self.use_transfer(self.not_used_transfer,
                                      self.resource_id,
                                      self.resource_transfer)

    transfer_creation_date = self.not_used_transfer['data']['date']
    transfer_modification_date = used_transfer['data']['date']

    self.assertEqual(
        used_transfer['data']['usedFor'],
        '/{}/{}'.format(self.resource_name, self.resource_id)
    )
    self.assertNotEqual(transfer_creation_date, transfer_modification_date)


def already_applied_transfer(self):
    auth = ('Basic', (self.first_owner, ''))
    self.__class__.resource_name = self.resource_name

    resource_which_use_transfer = self.create_resource(auth=auth)
    resource_which_use_transfer_access_transfer = self.resource_transfer

    resource_which_want_to_use_transfer = self.create_resource(auth=auth)
    resource_which_want_to_use_transfer_access_transfer = self.resource_transfer

    self.__class__.resource_name = ''

    transfer = self.create_transfer()
    self.use_transfer(transfer,
                      resource_which_use_transfer['id'],
                      resource_which_use_transfer_access_transfer)

    req_data = {
        "data":
            {"id": transfer['data']['id'],
             'transfer': resource_which_want_to_use_transfer_access_transfer}
    }
    req_url = '{}/{}/ownership'.format(
        self.resource_name,
        resource_which_want_to_use_transfer['id']
    )
    response = self.app.post_json(req_url, req_data, status=403)

    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Transfer already used',
         u'location': u'body',
         u'name': u'transfer'}])


def half_applied_transfer(self):
    # simulate half-applied transfer activation process (i.e. transfer
    # is successfully applied to a resource and relation is saved in transfer,
    # but resource is not stored with new credentials)
    auth = ('Basic', (self.first_owner, ''))

    self.__class__.resource_name = self.resource_name
    resource = self.create_resource(auth=auth)
    resource_access_transfer = self.resource_transfer
    self.__class__.resource_name = ''

    self.app.authorization = ('Basic', (self.second_owner, ''))
    transfer = self.create_transfer()
    transfer_doc = self.db.get(transfer['data']['id'])

    transfer_doc['usedFor'] = '/{}/{}'.format(
        self.resource_name, resource['id']
    )
    self.db.save(transfer_doc)
    self.use_transfer(transfer,
                      resource['id'],
                      resource_access_transfer)
    resource_which_used_transfer = self.get_resource(resource['id'])
    self.assertEqual(
        self.second_owner, resource_which_used_transfer['data']['owner']
    )


def new_owner_can_change(self):
    auth = ('Basic', (self.first_owner, ''))

    self.__class__.resource_name = self.resource_name
    resource = self.create_resource(auth=auth)
    resource_access_transfer = self.resource_transfer
    self.__class__.resource_name = ''

    self.app.authorization = ('Basic', (self.second_owner, ''))
    transfer = self.create_transfer()
    self.use_transfer(transfer,
                      resource['id'],
                      resource_access_transfer)

    new_access_token = transfer['access']['token']

    # second_owner can change the resource
    desc = "second_owner now can change the resource"
    req_data = {"data": {"description": desc}}
    req_url = '{}/{}?acc_token={}'.format(
        self.resource_name, resource['id'], new_access_token
    )
    response = self.app.patch_json(req_url, req_data)

    self.assertEqual(response.status, '200 OK')
    self.assertNotIn('transfer', response.json['data'])
    self.assertNotIn('transfer_token', response.json['data'])
    self.assertIn('owner', response.json['data'])
    self.assertEqual(response.json['data']['description'], desc)
    self.assertEqual(response.json['data']['owner'], self.second_owner)


def old_owner_cant_change(self):
    auth = ('Basic', (self.first_owner, ''))

    self.__class__.resource_name = self.resource_name
    resource = self.create_resource(auth=auth)
    resource_access_transfer = self.resource_transfer
    resource_access_token = self.resource_token
    self.__class__.resource_name = ''

    self.app.authorization = ('Basic', (self.second_owner, ''))
    transfer = self.create_transfer()

    self.use_transfer(transfer,
                      resource['id'],
                      resource_access_transfer)

    # fist_owner can`t change the resource
    desc = "make resource great again"
    req_data = {"data": {"description": desc}}
    req_url = '{}/{}?acc_token={}'.format(
        self.resource_name, resource['id'], resource_access_token
    )
    response = self.app.patch_json(req_url, req_data, status=403)
    self.assertEqual(response.status, '403 Forbidden')


def broker_not_accreditation_level(self):
    # try to use transfer by broker without appropriate accreditation level
    self.app.authorization = ('Basic', (self.invalid_owner, ''))

    transfer = self.create_transfer()
    req_data = {"data": {"id": transfer['data']['id'],
                         'transfer': self.resource_transfer}}
    req_url = '{}/{}/ownership'.format(self.resource_name, self.resource_id)

    response = self.app.post_json(req_url, req_data, status=403)

    self.assertEqual(response.json['errors'], [
        {u'description': u'Broker Accreditation level '
                         u'does not permit ownership change',
         u'location': u'body', u'name': u'data'}])


def level_permis(self):
    # test level permits to change ownership for 'test' resources

    self.app.authorization = ('Basic', (self.test_owner, ''))
    transfer = self.create_transfer()

    req_data = {"data": {"id": transfer['data']['id'],
                         'transfer': self.resource_transfer}}
    req_url = '{}/{}/ownership'.format(self.resource_name, self.resource_id)

    response = self.app.post_json(req_url, req_data, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Broker Accreditation level does'
                         u' not permit ownership change',
         u'location': u'body', u'name': u'data'}])


def switch_mode(self):
    # set test mode and try to change ownership

    auth = ('Basic', (self.first_owner, ''))

    self.__class__.resource_name = self.resource_name
    resource = self.create_resource(auth=auth)
    resource_access_transfer = self.resource_transfer
    self.__class__.resource_name = ''

    self.set_resource_mode(resource['id'], 'test')

    self.app.authorization = ('Basic', (self.test_owner, ''))
    transfer = self.create_transfer()

    req_data = {"data": {"id": transfer['data']['id'],
                         'transfer': resource_access_transfer}}
    req_url = '{}/{}/ownership'.format(self.resource_name, resource['id'])

    response = self.app.post_json(req_url, req_data)

    self.assertEqual(response.status, '200 OK')
    self.assertIn('owner', response.json['data'])
    self.assertEqual(response.json['data']['owner'], self.test_owner)
