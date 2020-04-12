import os
import logging
import re
import requests
import sys


from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse


logger = logging.getLogger('django_test')


class TestIdentity(TestCase):
    def setUp(self):
        pass
        #logger.info('{} SP: {}'.format(self.__class__.__name__,
                                       #self.client))

    def create_identity_radcheck(self):
        pass
        #data = dict(username='admin',
                    #email='test@test.org',
                    #is_superuser=1,
                    #is_staff=1)
        #user = get_user_model().objects.get_or_create(**data)[0]
        #user.set_password('admin')
        #user.save()
        #return user

    def activate_token(self):
        pass

    def radcheck_login(self):
        user = self._get_superuser_user()
        self.client.force_login(user)

    def reset_password(self):
        self._superuser_login()
        # put md store through admin UI
        create_url = reverse('admin:uniauth_metadatastore_add')
        data = dict(name='sptest',
                    type='local',
                    url=idp_md_path,
                    kwargs='{}',
                    is_active=1)
        response = self.client.post(create_url, data, follow=True)
        assert 'was added successfully' in response.content.decode()

        # put sp metadata into IDP md store
        sp_metadata = entity_descriptor(self.sp_conf)
        with open(IDP_SP_METADATA_PATH+'/sp.xml', 'wb') as fd:
            fd.write(sp_metadata.to_string())

    def other(self):
        self._superuser_login()
        create_url = reverse('admin:uniauth_serviceprovider_add')
        data = dict(entity_id = SAML_SP_CONFIG['entityid'],
                    display_name = 'That SP display name',
                    signing_algorithm = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
                    digest_algorithm = "http://www.w3.org/2001/04/xmlenc#sha256",
                    disable_encrypted_assertions=1,
                    is_active=1)
        response = self.client.post(create_url, data, follow=True)
        assert 'was added successfully' in response.content.decode()
