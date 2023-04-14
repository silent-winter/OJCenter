"""OJcenter URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView

from OJcenter import view, view_captcha, adminview

urlpatterns = [
    # path('admin/', admin.site.urls),
    # # path("/", include("frontend.urls")),
    # path('', views.login),
    # url(r'^login', views.login),
    # url(r'^vscode', views.login),
    # url(r'^info', views.info),
    # url(r'^cds', views.accessCodeServer),
    # url(r'^getcookie', view.getAccessCodeServer),
    # url(r'^permission', views.Permission),
    # url(r'^codeview', views.vscode),
    # url(r'^logout', views.logout),
    url(r'^.*getcookiesimple', view.getAccessCodeServerSimple),
    # url(r'^.*getcookie', view.getCookie),
    url(r'^.*insertuser', view.insertUser),
    url(r'^.*getorder', view.getOrder),
    url(r'^.*checkalive', view.checkAlive),
    url(r'^.*checkstatus', view.checkStatus),
    url(r'^.*removeuser', view.removeUser),
    url(r'^.*getuserport', view.getUserPort),
    url(r'^.*getusertoken', view.getUserToken),
    url(r'^.*getusetime', view.getUseTime),
    url(r'^.*submitanswer', view.getSubmitAnswer),
    url(r'^.*editcode', view.getEditCode),
    url(r'^.*update', view.getEditCodeUpdate),
    # url(r'^entercontest', view.entercontest),
    url(r'^.*getusername', view.getUsername),
    url(r'^.*onlinecount', view.onlinecount),
    url(r'^.*checkmessage', view.getMessage),
    url(r'^.*getmodel', view.getModel),
    url(r'^.*getlasturl', view.getUrl),

    url(r'^.*userlist', adminview.userlist),
    url(r'^.*usermonitor', adminview.usermonitor),

    re_path(r'^.*captcha/hashkey/?$', view_captcha.captcha_hashkey),
    re_path(r'^.*captcha/image/(\w+)/?$', view_captcha.captcha_image),
    re_path(r'^.*captcha/check-captcha/?$', view_captcha.check_captcha),
]

view.init()
