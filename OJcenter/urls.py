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
    url(r'^k8s-admin/', include('k8s_admin.urls')),
    # path('k8s_admin/', k8s_admin.site.urls),
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
    path('getcookiesimple', view.getAccessCodeServerSimple),
    # ur(.*getcookie', view.getCookie),
    path('insertuser', view.insertUser),
    path('getorder', view.getOrder),
    path('checkalive', view.checkAlive),
    url(r'^checkstatus', view.checkStatus),
    path('removeuser', view.removeUser),
    path('getuserport', view.getUserPort),
    path('getusertoken', view.getUserToken),
    path('getusetime', view.getUseTime),
    path('submitanswer', view.getSubmitAnswer),
    path('editcode', view.getEditCode),
    path('update', view.getEditCodeUpdate),
    # ur(entercontest', view.entercontest),
    path('getusername', view.getUsername),
    path('onlinecount', view.onlinecount),
    path('checkmessage', view.getMessage),
    url(r'^getmodel', view.getModel),
    url(r'^getlasturl', view.getUrl),
    url(r'^notice', view.handleNotice),
    path(r'lockstatus', view.lockStatus),

    path('userlist', adminview.userlist),
    path('usermonitor', adminview.usermonitor),

    re_path(r'^captcha/hashkey/?$', view_captcha.captcha_hashkey),
    re_path(r'^captcha/image/(\w+)/?$', view_captcha.captcha_image),
    re_path(r'^captcha/check-captcha/?$', view_captcha.check_captcha),
]

view.init()
