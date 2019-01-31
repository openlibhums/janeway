INSTALLED_APPS= ["django_nose"]

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_ARGS = [
    '--with-xunit',
    '--xunit-file=jenkins/nosetests.xml',
]
