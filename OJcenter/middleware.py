from django.shortcuts import HttpResponse
from django.utils.deprecation import MiddlewareMixin

from OJcenter.Tool import systemTool

login_list = ['/insertuser', '/getorder', '/checkstatus', '/checkalive', '/removeuser', '/getuserport',
              '/getusertoken', '/getusetime', '/editcode', '/getusername', '/onlinecount', '/checkmessage',
              '/getmodel', '/getlasturl', '/lockstatus']


class LoginMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path in login_list:
            username = systemTool.checkLogin(request)
            if username:
                request.username = username
                pass
            else:
                return HttpResponse(status=401)

