# Source snapshot: django/django
# Upstream: https://github.com/django/django/blob/414aa38de3ca5ebabda300325efaa7b274a53771/django/http/request.py
content_length = int(self.META.get("CONTENT_LENGTH") or 0)
# Limit the maximum request data size that will be handled in-memory.
# Reject early when Content-Length is present and already exceeds the limit.
self._check_data_too_big(content_length)
if self._stream.seekable():
    stream_size = self._stream.seek(0, os.SEEK_END)
    self._check_data_too_big(stream_size)
self._body = self.read()
