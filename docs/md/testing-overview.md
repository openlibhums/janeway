# Testing Janeway

Janeway uses a blend of unit tests, regression tests, and end-to-end tests, run using the Django unittest framework.

## Organization

Tests are laid out by app. Sometimes a test has to work across apps, but we try to avoid that if possible.

In some apps we only have a few tests in a `tests.py` file, but as we add tests, we split the files out by the part of the app tested, so `tests/test_views.py` and `tests/test_models.py`.

Here is a list of apps with tests:

* copyediting
* core
* cron
* identifiers
* journal
* metrics
* press
* production
* proofing
* repository
* review
* security
* submission
* typesetting
* utils

## Tips

1. Speed up testing by passing `DB_VENDOR=sqlite`. This will skip migrations.
2. For each TestCase subclass, set up data using `setUpTestData` or `setUp`. Try to avoid creating objects or doing things that will be cached and have side effects in the actual test functions, since side effects are difficult to track down. If you do create side effects, remove them by defining a `tearDown` function.
3. Use `testing/helpers.py` where possible to create objects in `setUpTestData`, so that the test data is more consistent across Janeway.
4. Keep tests self-contained by using `mock` sparingly. It is especially helpful in cases where the function being tested interacts with parts of the codebase that are not being tested.
