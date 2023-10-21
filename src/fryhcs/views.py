from http import HTTPStatus
from django.http import Http404, HttpResponse, StreamingHttpResponse
from django.conf import settings

import json
import logging
import uuid

logger = logging.getLogger('frycss.views')


server_id = uuid.uuid4().hex

def update_serverid():
    global server_id
    server_id = uuid.uuid4().hex

def message():
    return f'data: {{"serverId": "{server_id}"}}\n\n'.encode()

def check_hotreload(request):
    if not settings.DEBUG:
        raise Http404()
    if not request.accepts('text/event-stream'):
        return HttpResponse(status=HTTPStatus.NOT_ACCEPTABLE)
    def event_stream():
        # 立刻发送一个响应消息，触发浏览器EventSource的open事件。
        yield message()
        while True:
            time.sleep(0.5)
            # 定期发送消息，两个用途：
            # 1. 检测浏览器页面是否已关闭，关闭则结束这个链接
            # 2. 告诉浏览器自己还活着
            yield message()

    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream',
    )
    response['content-encoding'] = ''
    return response

def components(request):
    pass
