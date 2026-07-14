import os
import re


class RangeFileMiddleware:
    """
    Enables HTTP Range requests for media files served by Django dev server.
    This fixes video seeking/dragging in Chrome when videos are stored locally.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only process media file responses
        if not request.path.startswith('/media/'):
            return response

        # Only process video/audio files
        content_type = response.get('Content-Type', '')
        if 'video' not in content_type and 'audio' not in content_type:
            return response

        # If browser sends a Range header, handle it
        range_header = request.META.get('HTTP_RANGE', '')
        if not range_header:
            # No range request — just add Accept-Ranges header so browser knows it can seek
            response['Accept-Ranges'] = 'bytes'
            return response

        # Parse Range header: "bytes=start-end"
        match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if not match:
            return response

        # Get full content
        if hasattr(response, 'streaming_content'):
            content = b''.join(response.streaming_content)
        else:
            content = response.content

        total_size = len(content)
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else total_size - 1
        end = min(end, total_size - 1)
        chunk = content[start:end + 1]
        chunk_size = len(chunk)

        from django.http import HttpResponse
        range_response = HttpResponse(
            chunk,
            status=206,
            content_type=content_type
        )
        range_response['Content-Range'] = f'bytes {start}-{end}/{total_size}'
        range_response['Accept-Ranges'] = 'bytes'
        range_response['Content-Length'] = str(chunk_size)
        return range_response