from http import HTTPStatus
from django.http import Http404, HttpResponse, StreamingHttpResponse
from django.conf import settings

from fryhcs.reload import event_stream, mime_type

import logging
import uuid

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

def components(request):
    pass
