from django.conf import settings
from django.db.models import Count
from six import text_type

from opaque_keys.edx.keys import CourseKey

from analyticsclient.client import Client
from analyticsclient.exceptions import NotFoundError
from courseware import models
from student.models import CourseAccessRole
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata


# exclude these in Metrics
NON_STUDENT_ROLES = [
    'instructor',
    'staff',
]
PROB_TYPE_LIST = [
    'problem',
    'lti',
]


def construct_problem_data(prob_grade_distrib, total_student_count, c_subsection, c_unit, c_problem, component):
    """
    Returns dict of problem with student grade data.

    `prob_grade_distrib` Dict of grade distribution for all problems in the course.
    `total_student_count` Dict of number of students attempting each problem.
    `c_subsection` Incremental subsection count.
    `c_unit` Incremental unit count.
    `c_problem` Incremental problem count.
    `component` The component for which data is being returned.

    Returns a dict of problem label and data for use in d3 rendering.
    """
    c_problem += 1
    stack_data = []

    # Construct label to display for this problem
    label = "P{0}.{1}.{2}".format(c_subsection, c_unit, c_problem)

    if component.location in prob_grade_distrib:
        problem_info = prob_grade_distrib[component.location]

        # Get problem_name for tooltip
        problem_name = own_metadata(component).get('display_name', '')

        # Compute percent of this grade over max_grade
        max_grade = float(problem_info['max_grade'])
        for (grade, count_grade) in problem_info['grade_distrib']:
            percent = 0.0
            if max_grade > 0:
                percent = round((grade * 100.0) / max_grade, 1)

            # Compute percent of students with this grade
            student_count_percent = 0

            if total_student_count[component.location] > 0:
                student_count_percent = count_grade * 100 / total_student_count[component.location]

            # Tooltip parameters for problem in grade distribution view
            tooltip = {
                'type': 'problem',
                'label': label,
                'problem_name': problem_name,
                'count_grade': count_grade,
                'percent': percent,
                'grade': grade,
                'max_grade': max_grade,
                'student_count_percent': student_count_percent,
            }

            # Construct data to be sent to d3
            stack_data.append({
                'color': percent,
                'value': count_grade,
                'tooltip': tooltip,
                'module_url': text_type(component.location),
            })

    problem = {
        'xValue': label,
        'stackData': stack_data,
    }
    return problem, c_problem


def get_non_student_list(course_key):
    """
    Find all user_ids with instructor or staff roles in student_courseaccessrole table
    """
    non_students = CourseAccessRole.objects.filter(
        course_id=course_key,
        role__in=NON_STUDENT_ROLES,
    ).values('user_id').distinct()
    return [
        non_student['user_id']
        for non_student in non_students
    ]


def get_non_student_list_from_request(request):
    """
    Find all user_ids with instructor or staff roles in student_courseaccessrole table
    """
    course_id = request.GET.get('course_id')
    course_key = CourseKey.from_string(course_id)
    module_state_key = course_key.make_usage_key_from_deprecated_string(request.GET.get('module_id'))
    users = get_non_student_list(course_key)
    return users


def get_problem_set_grade_distrib_api(course_id, problem_set):
    course_key = CourseKey.from_string(course_id)
    enrollment = CourseEnrollment.objects.enrollment_counts(course_key)
    prob_grade_distrib = None
    if enrollment <= settings.MAX_ENROLLEES_FOR_METRICS_USING_DB or not settings.ANALYTICS_API_URL:
        # Aggregate query on studentmodule table for grade data for set of problems in course
        queryset = models.StudentModule.objects.filter(
            course_id__exact=course_id,
            grade__isnull=False,
            module_type__in=PROB_TYPE_LIST,
            module_state_key__in=problem_set,
        ).exclude(student_id__in=non_student_list).values(
            'module_state_key',
            'grade',
            'max_grade',
        ).annotate(count_grade=Count('grade')).order_by('module_state_key', 'grade')

        client = Client(base_url=settings.ANALYTICS_API_URL, auth_token=settings.ANALYTICS_API_KEY)
        for problem in problem_set:
            module = client.modules(course_id, problem)

            try:
                grade_distribution = module.grade_distribution()
            except NotFoundError:
                grade_distribution = []

            prob_grade_distrib = {}
            for score in grade_distribution:
                if problem in prob_grade_distrib:
                    if prob_grade_distrib[problem]['max_grade'] < score['max_grade']:
                        prob_grade_distrib[problem]['max_grade'] = score['max_grade']

                    prob_grade_distrib[problem]['grade_distrib'].append((score['grade'], score['count']))
                else:
                    prob_grade_distrib[problem] = {
                        'max_grade': score['max_grade'],
                        'grade_distrib': [(score['grade'], score['count'])],
                    }
        return prob_grade_distrib


def get_problem_grade_distribution_api(course_id):
    prob_grade_distrib = None
    total_student_count = None
    enrollment = CourseEnrollment.objects.enrollment_counts(course_key)
    if enrollment <= settings.MAX_ENROLLEES_FOR_METRICS_USING_DB or not settings.ANALYTICS_API_URL:
        db_query = models.StudentModule.objects.filter(
            course_id__exact=course_id,
            grade__isnull=False,
            module_type__exact="problem",
        ).exclude(
            student_id__in=get_non_student_list(course_id),
        ).values('module_state_key', 'grade', 'max_grade').annotate(count_grade=Count('grade'))

        # Retrieve course object down to problems
        course = modulestore().get_course(course_id, depth=4)

        # Connect to analytics data client
        client = Client(base_url=settings.ANALYTICS_API_URL, auth_token=settings.ANALYTICS_API_KEY)

        prob_grade_distrib = {}
        total_student_count = {}
        for section in course.get_children():
            for subsection in section.get_children():
                for unit in subsection.get_children():
                    for child in unit.get_children():
                        if child.location.category not in PROB_TYPE_LIST:
                            continue

                        problem_id = child.location
                        problem = client.modules(course_id, problem_id)

                        try:
                            grade_distribution = problem.grade_distribution()
                        except NotFoundError:
                            grade_distribution = []

                        for score in grade_distribution:
                            total_student_count[problem_id] += score['count']

                            if problem_id in prob_grade_distrib:
                                if prob_grade_distrib[problem_id]['max_grade'] < score['max_grade']:
                                    prob_grade_distrib[problem_id]['max_grade'] = score['max_grade']

                                prob_grade_distrib[problem_id]['grade_distrib'].append((score['grade'], score['count']))
                            else:
                                prob_grade_distrib[problem_id] = {
                                    'max_grade': score['max_grade'],
                                    'grade_distrib': [(score['grade'], score['count']), ],
                                }
    return prob_grade_distrib, total_student_count
