from django.db import models


class UserstatusDetail(models.Model):
    username = models.CharField(max_length=255, blank=True, null=True)
    contest_id = models.CharField(max_length=255, blank=True, null=True)
    problem_id = models.CharField(max_length=255, blank=True, null=True)
    teacher_label = models.IntegerField(blank=True, null=True)
    is_lock = models.IntegerField(blank=True, null=True)
    is_unlock = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'userstatus_detail'


class PodMetaInfo:
    def __init__(self, ip, port, name, pvPath):
        self.ip = ip
        self.port = port
        self.name = name
        self.pvPath = pvPath

    def __repr__(self):
        return "ip=%s, port=%s, name=%s, pvPath=%s" % (self.ip, self.port, self.name, self.pvPath)
