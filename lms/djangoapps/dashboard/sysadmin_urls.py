"""
Urls for sysadmin dashboard feature
"""

from django.conf.urls import url

from dashboard import sysadmin

urlpatterns = [
    url(r'^$', sysadmin.Users.as_view(), name="sysadmin"),
    url(r'^courses/?$', sysadmin.Courses.as_view(), name="sysadmin_courses"),
    url(r'^staffing/?$', sysadmin.Staffing.as_view(), name="sysadmin_staffing"),
    url(r'^gitlogs/?$', sysadmin.GitLogs.as_view(), name="gitlogs"),
    url(r'^gitlogs/(?P<course_id>.+)$', sysadmin.GitLogs.as_view(),
        name="gitlogs_detail"),
<<<<<<< HEAD
    url(r'^task_queue/?$', sysadmin.TaskQueue.as_view(), name="sysadmin_task_queue"),
    url(r'^mgmt_commands/?$', sysadmin.MgmtCommands.as_view(), name="sysadmin_mgmt_commands"),
)
=======
]
>>>>>>> 7ad437b52cb5b2d65ab1b65e6147bcced05c42e4
