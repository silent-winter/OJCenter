from django.conf.urls import url

from k8s_admin import views

urlpatterns = [
    url(r'^user/list', views.list_user),
    url(r'^node/list', views.list_node),
    url(r'^history/list', views.list_for_user_history),
    url(r'^migrate/(.*)', views.migrate),
    url(r'^kick/(.*)', views.kick),
    url(r'^resource/(.*)', views.list_for_resource),
]

views.init()
