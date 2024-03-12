INSTALLED_APPS = ["django_nose"]
MERGEABLE_SETTINGS = {"INSTALLED_APPS"}

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_ARGS = [
    '--with-xunit',
    '--xunit-file=jenkins/nosetests.xml',
]
