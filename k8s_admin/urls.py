from django.conf.urls import url

from k8s_admin import views

urlpatterns = [
    url(r'^list', views.list_for_data),
    url(r'^migrate/(.*)', views.migrate),
    url(r'kick/(.*)', views.kick)
]
