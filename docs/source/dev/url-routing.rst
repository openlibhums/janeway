URL Routing
===========

Preserving app state with the next parameter
--------------------------------------------

Users often have a main task (e.g. submit an article) and a side task (e.g. log in / register) that they need to complete during the main task.

When Janeway invites them to start the side task, it registers the URL of the main task on a `next` parameter, like Django does by default. Then at the end of the side task, it redirects them to the main task, so they can pick back up where they left off.

Login and registration are a common side task, but Janeway does not use Django’s built-in `auth_views` because of legacy reasons and the need to support authentication via third-party services like ORCiD and OpenID Connect (OIDC). As a result, we handle `next` via custom template tags and explicit checks in the associated views.

  1. To initiate a `next` parameter in the main task template, use the `url_with_return` template tag (not the normal `url` tag) to form the URL that begins the side task. This will capture the current request URL as the return destination. Note that this can be recursive: you can initiate a side task from a side task, and the current next URL will be nested properly and encoded safely within the query string of the new URL that will be assigned to `next`.

  2. Then, to preserve that `next` parameter through a sequence of views and templates, use the `url_with_next` template tag. Note: there is also a variant called `url_with_next_and_orcid_action` for situations where the ORCiD action needs to be passed as well.

In all views related to the side task, make sure to check the GET request parameters for `next`, and pass them along in one of two ways:

  * If redirecting to another step in the side task: use `logic.reverse_with_next` when reversing the URL.

  * If the side task is concluded, redirect to the value of `next`.

Note that the `next` state is always transmitted as GET request parameter, and so it will always be visible in the query string. This is possible because Django makes GET parameters from the query string in the HTTP header available even when the request method is POST. Successive requests to the same endpoint will not remove or change the query string, even if the request method changes; only redirects in the view, or reformations of an `href` or form `action` in the template, can change it. While it is not often desirable to make use of both GET and POST data, we do it intentionally here for a few reasons: the `next` pattern is consistent across views, and we avoid interfering with the payload of actual form data sent via POST.
