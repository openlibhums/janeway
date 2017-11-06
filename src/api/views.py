import json

from django.http import HttpResponse
from django.shortcuts import render

from rest_framework import viewsets, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions

from api import serializers, permissions as api_permissions
from core import models as core_models
from submission import models as submission_models


@api_view(['GET'])
@permission_classes((permissions.AllowAny, ))
def index(request):
    response_dict = {
        'Message': 'Welcome to the API',
        'Version': '1.0',
        'API Endpoints':
            [],
    }
    json_content = json.dumps(response_dict)

    return HttpResponse(json_content, content_type="application/json")


@permission_classes((api_permissions.IsEditor, ))
class AccountRoleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows user roles to be viewed or edited.
    """
    queryset = core_models.AccountRole.objects.filter()
    serializer_class = serializers.AccountRoleSerializer


def oai(request):
    articles = submission_models.Article.objects.filter(stage=submission_models.STAGE_PUBLISHED)

    template = 'apis/OAI.xml'
    context = {
        'articles': articles,
    }

    return render(request, template, context, content_type="application/xml")
