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
