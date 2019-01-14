INSTALLED_APPS= ["django_nose"]

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_ARGS = [
    '--with-xunit',
    '--cover-erase',
    '--cover-package=janeway', # Change `MY_APP` to your `app` name
]
