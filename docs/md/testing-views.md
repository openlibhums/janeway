# Testing views

> [!NOTE]
> This page assumes familiarity with writing automated tests in Python.

When writing tests for Janeway views, rely on the Django test client (`django.test.Client`) unless the nature of your test requires dealing with requests objects explicitly.

Here are tips for avoiding common pitfalls and saving debugging time.

## Setting up a user for login-protected views

Use `force_login` to log the test user in before accessing a protected view.

> [!NOTE]
> The user must be active (`is_active=True`) for this to work.

```py
from django.test import TestCase

class MyTest(TestCase):

    def my_test(self):
        user.is_active = True
        user.save()
        self.client.force_login(user)
```

## Use domain mode explicitly

To call the Django test client, you have to write out the URL. But in Janeway, URLs are interpreted differently based on the `URL_CONFIG` setting. `URL_CONFIG` can be set to `"path"` or `"domain"`. In most cases, it is best to set `"domain"` using a setting override in a decorator, so you do not have to write out the journal code or repository short name in the URL.

```py
from django.test import TestCase, override_settings

class MyTest(TestCase):
    @override_settings(URL_CONFIG="domain")
    def my_test(self):
        url = "/profile/"
```

## Name the test server

When Janeway is using domain mode, the domain of the website you are testing (press, journal, repository) becomes important. So it is a good idea to explicitly pass the name of the target domain as `SERVER_NAME` when calling the client.

```py
from django.test import TestCase

class MyTest(TestCase):
    def my_test(self):
        response = self.client.get(
            "/profile/",
            SERVER_NAME="www.example.org",
        )
```

## When to clear the "script prefix"

In path mode, Janeway makes use of `django.urls.base.set_script_prefix` to insert the journal code into request URLs. However, this path prefix does not go away when another request is made in domain mode. You have to manually clear it by using `clear_script_prefix` in the `tearDown` method of any test case where path mode is used.

```py
from django.urls.base import clear_script_prefix
from django.test import TestCase

class MyTest(TestCase):
    def tearDown(self):
        clear_script_prefix()
```

If the offending test cannot be found, you can remove the prefix in the `setUp` of any affected test cases.

```py
    def setUp(self):
        clear_script_prefix()
```

## How to clear the cache

Sometimes a test is affected by cached data. If needed you can clear the main
cache in your setup method or the main test:

```py
from utils.shared import clear_cache

clear_cache()
```

## Testing views with captchas

Captchas are inserted depending on the `CAPTCHA_TYPE` Django setting, and forms that require them will come up invalid in tests. Disable the captcha during a test run by overriding the setting with an empty string:

```
    @override_settings(CAPTCHA_TYPE="")
    def test_posting_view_with_captcha(self):
        ...
```
