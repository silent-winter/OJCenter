import re

from django.shortcuts import HttpResponse
from django.utils.deprecation import MiddlewareMixin

from OJcenter.Tool import systemTool


class AdminMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if re.match(r'^/k8s-admin/.*', request.path):
            session_id = systemTool.get_session_id(request)
            if session_id and systemTool.is_admin(session_id):
                pass
            else:
                return HttpResponse(status=401)
