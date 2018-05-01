'''
django admin pages for courseware model
'''

<<<<<<< HEAD
from courseware.models import CoursePreference
from courseware.models import StudentModule, OfflineComputedGrade, OfflineComputedGradeLog
=======
>>>>>>> f9fa460a74446b533b356e754848af6f56c141a1
from ratelimitbackend import admin

from courseware.models import OfflineComputedGrade, OfflineComputedGradeLog, StudentModule

admin.site.register(StudentModule)

admin.site.register(OfflineComputedGrade)

admin.site.register(OfflineComputedGradeLog)

admin.site.register(CoursePreference)
