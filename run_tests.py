#!/usr/bin/env python
import sys
from coverage import coverage
from optparse import OptionParser

from django.conf import settings


if not settings.configured:
    datacash_settings = {}
    try:
        from integration import *
    except ImportError:
        datacash_settings.update({
            'DATACASH_HOST': 'testserver.datacash.com',
            'DATACASH_CLIENT': '',
            'DATACASH_PASSWORD': '',
            'DATACASH_CURRENCY': 'GBP',
            'DATACASH_USE_CV2AVS': True,
        })
    else:
        for key, value in locals().items():
            if key.startswith('DATACASH'):
                datacash_settings[key] = value
                
    settings.configure(
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    }
                },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.admin',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.sites',
                'datacash',
                'south',
                ],
            DEBUG=False,
            SITE_ID=1,
            NOSE_ARGS=['-s', '--with-spec'],
            **datacash_settings
        )

# Needs to be here to avoid missing SETTINGS env var
from django_nose import NoseTestSuiteRunner


def run_tests(*test_args):
    if 'south' in settings.INSTALLED_APPS:
        from south.management.commands import patch_for_test_db_setup
        patch_for_test_db_setup()

    if not test_args:
        test_args = ['tests']

    # Run tests
    test_runner = NoseTestSuiteRunner(verbosity=1)

    c = coverage(source=['datacash'], omit=['*migrations*', '*tests*'])
    c.start()
    num_failures = test_runner.run_tests(test_args)
    c.stop()

    if num_failures > 0:
        sys.exit(num_failures)
    print "Generating HTML coverage report"
    c.html_report()


def generate_migration():
    from south.management.commands.schemamigration import Command
    com = Command()
    com.handle(app='datacash', initial=True)


if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    run_tests(*args)
