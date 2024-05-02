from django.contrib.admin.apps import AdminConfig


class JanewayAdminConfig(AdminConfig):
    default_site = 'admin.JanewayAdminSite'
