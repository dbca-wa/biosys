from .base import *

# Additional apps required for testing.
INSTALLED_APPS += (
    'django_nose',
)

# Test runner settings.
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = [
    '--nocapture',
    '--nologcapture',
    '--with-fixture-bundling',
    '--with-coverage',
    '--cover-package=main',
    '--verbosity=2',
    '--detailed-errors']
