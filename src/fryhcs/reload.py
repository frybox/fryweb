import uuid
import time

server_id = uuid.uuid4().hex

def update_serverid():
    global server_id
    server_id = uuid.uuid4().hex

def message():
    return f'data: {{"serverId": "{server_id}"}}\n\n'

def event_stream():
    # 立刻发送一个响应消息，触发浏览器EventSource的open事件。
    yield message()
    while True:
        time.sleep(0.5)
        # 定期发送消息，两个用途：
        # 1. 检测浏览器页面是否已关闭，关闭则结束这个链接
        # 2. 告诉浏览器自己还活着
        yield message()

mime_type = 'text/event-stream'
