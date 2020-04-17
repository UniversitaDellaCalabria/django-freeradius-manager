import os
import logging
import re
import requests
import sys

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from django_freeradius.models import RadiusCheck, encode_secret
from identity.models import Identity

logger = logging.getLogger('django_test')


class TestIdentity(TestCase):
    def setUp(self):
        data = dict(name='giulio',
                    email='test@test.org',
                    surname='cesare')
        self.raduser, self.radpass = 'test', 'value'
        self.identity = Identity.objects.create(**data)
        self.radcheck = RadiusCheck.objects.create(username=self.raduser,
                                                   value=encode_secret(new_value=self.radpass),
                                                   valid_until=timezone.now()+timezone.timedelta(days=365))
        self.identity.create_token(self.radcheck)

    def test_radcheck(self):
        data = dict(username=self.raduser,
                    password=self.radpass)
        _url = reverse('identity:login')
        response = self.client.post(_url, data, follow=True)
        assert 'Authentication failed' not in response.content.decode()

    def test_token(self):
        _url = reverse('identity:renew-radius-password',
                       kwargs={'token_value': self.identity.identityradiusaccount_set.first().token})
        response = self.client.get(_url, follow=True)
        assert 'Renew Password' in response.content.decode()

        _url_2 = reverse('identity:change_password',
                         kwargs=dict(radcheck_id=self.radcheck.pk))

        data = dict(username=self.radcheck.username,
                    password='IngolaBus34-',
                    password_verifica='IngolaBus34-')
        response_2 = self.client.post(_url, data=data,follow=True)
        assert 'succesfully renewed' in response.content.decode()
