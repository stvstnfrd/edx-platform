from django.contrib import admin

from config_models.admin import ConfigurationModelAdmin, KeyedConfigurationModelAdmin

<<<<<<< HEAD
from courseware.models import CoursePreference
from courseware.models import OfflineComputedGrade, OfflineComputedGradeLog, StudentModule

admin.site.register(StudentModule)

admin.site.register(OfflineComputedGrade)

admin.site.register(OfflineComputedGradeLog)

admin.site.register(CoursePreference)
=======
from courseware import models

admin.site.register(models.DynamicUpgradeDeadlineConfiguration, ConfigurationModelAdmin)
admin.site.register(models.OfflineComputedGrade)
admin.site.register(models.OfflineComputedGradeLog)
admin.site.register(models.CourseDynamicUpgradeDeadlineConfiguration, KeyedConfigurationModelAdmin)
admin.site.register(models.OrgDynamicUpgradeDeadlineConfiguration, KeyedConfigurationModelAdmin)
admin.site.register(models.StudentModule)
>>>>>>> 7ad437b52cb5b2d65ab1b65e6147bcced05c42e4
