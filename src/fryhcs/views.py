from http import HTTPStatus
from django.http import Http404, HttpResponse, StreamingHttpResponse, JsonResponse
from django.conf import settings

from fryhcs.reload import event_stream, mime_type

from fryhcs import render

import logging
import uuid
import json

logger = logging.getLogger('frycss.views')


def check_hotreload(request):
    if not settings.DEBUG:
        raise Http404()
    if not request.accepts(mime_type):
        return HttpResponse(status=HTTPStatus.NOT_ACCEPTABLE)
    response = StreamingHttpResponse(
        event_stream(),
        content_type=mime_type,
    )
    response['content-encoding'] = ''
    return response

def component(request):
    if request.method == 'GET':
        data = request.GET
    elif request.method == 'POST':
        data = request.POST
    else:
        raise Http404()
    name = data.get('name')
    args = data.get('args')
    args = json.loads(args)
    element = render(name, **args)
    page = element.page
    return JsonResponse({
        'code': 0,
        'dom': str(element),
        'components': page.components,
    })
