from django.db import models


class UserstatusDetail(models.Model):
    username = models.CharField(max_length=255, blank=True, null=True)
    contest_id = models.CharField(max_length=255, blank=True, null=True)
    problem_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    pastetime = models.CharField(max_length=255, blank=True, null=True)
    paste_label = models.CharField(max_length=255, blank=True, null=True)
    detail = models.TextField(blank=True, null=True)
    paste_pre1 = models.TextField(blank=True, null=True)
    paste_pre2 = models.TextField(blank=True, null=True)
    paste = models.TextField(blank=True, null=True)
    paste_after1 = models.TextField(blank=True, null=True)
    paste_after2 = models.TextField(blank=True, null=True)
    teacher_label = models.IntegerField(blank=True, null=True)
    is_lock = models.IntegerField(blank=True, null=True)
    is_unlock = models.IntegerField(blank=True, null=True)
    updatetime = models.CharField(max_length=255, blank=True, null=True)
    autounlock_time = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'userstatus_detail'

class Notification(models.Model):
    content = models.TextField(db_collation='utf8_general_ci', blank=True, null=True)
    targetuser = models.CharField(max_length=255, blank=True, null=True)
    deadline = models.CharField(max_length=255, blank=True, null=True)
    contestid = models.CharField(max_length=255, blank=True, null=True)
    platform = models.CharField(max_length=255, blank=True, null=True)
    updatetime = models.DateTimeField(blank=True, null=True)
    adduser = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'notification'

class Notificationget(models.Model):
    username = models.CharField(max_length=255, blank=True, null=True)
    notificationid = models.IntegerField(blank=True, null=True)
    updatetime = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'notificationget'
