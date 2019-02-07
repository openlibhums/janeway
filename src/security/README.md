All security enforcement for Janeway is handled in the security app, either through decorators (for view methods) or through templatetags (for templates).

Although some of these methods raise Http404 or other Http status responses, these decorators are only meant to be applied to view functions.