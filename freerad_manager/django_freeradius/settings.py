import os

from django.conf import settings

FREERADIUS_EDITABLE_ACCOUNTING = getattr(settings, 'FREERADIUS_EDITABLE_ACCOUNTING', False)
FREERADIUS_EDITABLE_POSTAUTH = getattr(settings, 'FREERADIUS_EDITABLE_POSTAUTH', False)

FREERADIUS_DEFAULT_SECRET_FORMAT = getattr(settings,
                                'FREERADIUS_DEFAULT_SECRET_FORMAT',
                                'NT-Password')

FREERADIUS_DISABLED_SECRET_FORMATS = getattr(settings, 'FREERADIUS_DISABLED_SECRET_FORMATS', [])

FREERADIUS_RADCHECK_SECRET_VALIDATORS = getattr(settings,
                                     'FREERADIUS_RADCHECK_SECRET_VALIDATORS',
                                     {'regexp_lowercase': '[a-z]+',
                                      'regexp_uppercase': '[A-Z]+',
                                      'regexp_number': '[0-9]+',
                                      'regexp_special': '[\!\%\-_+=\[\]\
                                                        {\}\:\,\.\?\<\>\(\)\;]+'})
