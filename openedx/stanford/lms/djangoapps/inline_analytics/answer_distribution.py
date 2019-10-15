from datetime import datetime
import json

from django.conf import settings
from django.http import Http404
from django.http import HttpResponseNotFound
from django.http import HttpResponseServerError
from django.utils.translation import ugettext as _
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from pytz import timezone

from analyticsclient.client import Client
from analyticsclient.exceptions import NotFoundError, InvalidRequestError, TimeoutError
from courseware.access import has_access
from courseware.courses import get_course_with_access
from util.date_utils import get_time_display
from util.json_request import JsonResponse


def _format_date(data):
    """
    Format the created date
    """
    created_date = data[0]['created']
    obj_date = datetime.strptime(created_date, '%Y-%m-%dT%H%M%S')
    obj_date = timezone('UTC').localize(obj_date)
    formatted_date_string = get_time_display(obj_date, None, coerce_tz=settings.TIME_ZONE_DISPLAYED_FOR_DEADLINES)
    return formatted_date_string


def _get_error_message():
    """
    Construct an error message and link to Zendesk
    """
    if settings.ZENDESK_URL:
        url = '<a href="{zendesk_url}/hc/en-us/requests/new">'.format(
            zendesk_url=settings.ZENDESK_URL,
        )
        error_message = _(
            "A problem has occurred retrieving the data, to report the problem click "
            "{tag_start}here{tag_end}"
        ).format(
            tag_start=url,
            tag_end='</a>',
        )
    else:
        error_message = _('A problem has occurred retrieving the data.')
    return error_message


def _get_part_count(item, running_counts):
    """
    Calculate new running part count
    """
    counts = running_counts or {
        'totalFirstAttemptCount': 0,
        'totalFirstCorrectCount': 0,
        'totalFirstIncorrectCount': 0,
        'totalLastAttemptCount': 0,
        'totalLastCorrectCount': 0,
        'totalLastIncorrectCount': 0,
    }
    counts['totalFirstAttemptCount'] += item['first_response_count']
    counts['totalLastAttemptCount'] += item['last_response_count']
    if item['correct']:
        counts['totalFirstCorrectCount'] += item['first_response_count']
        counts['totalLastCorrectCount'] += item['last_response_count']
    else:
        counts['totalFirstIncorrectCount'] += item['first_response_count']
        counts['totalLastIncorrectCount'] += item['last_response_count']
    return counts


def _get_part_data(item):
    """
    Create a part dictionary
    """
    part_dict = {}
    part_dict['value_id'] = item['value_id']
    part_dict['correct'] = item['correct']
    part_dict['first_count'] = item['first_response_count']
    part_dict['last_count'] = item['last_response_count']
    return part_dict


def get_analytics_answer_dist(request):
    """
    Retrieve answer distribution data for inline analytics display via API

    Arguments:
        request: the Django HTTP request object that triggered this view function

    Returns:
        (django response object):
            500 if error occurred,
            404 if api client returns no data,
            otherwise 200 with JSON body
    """
    error_message = _get_error_message()
    if not settings.ANALYTICS_API_URL:
        return HttpResponseServerError(error_message)
    all_data = json.loads(request.body)
    module_id = all_data['module_id']
    question_types_by_part = all_data['question_types_by_part']
    num_options_by_part = all_data['num_options_by_part']
    course_key = SlashSeparatedCourseKey.from_string(all_data['course_id'])

    try:
        course = get_course_with_access(request.user, 'staff', course_key, depth=None)
    except Http404:
        return HttpResponseServerError(error_message)
    is_staff = has_access(request.user, 'staff', course)
    if not is_staff:
        return HttpResponseServerError(error_message)

    client = Client(base_url=settings.ANALYTICS_API_URL, auth_token=settings.ANALYTICS_API_KEY)
    module = client.modules(course.id, module_id)

    try:
        data = module.answer_distribution()
    except NotFoundError:
        return HttpResponseNotFound(_('There are no student answers for this problem yet; please try again later.'))
    except InvalidRequestError:
        return HttpResponseServerError(error_message)
    except TimeoutError:
        return HttpResponseServerError(error_message)
    return process_analytics_answer_dist(data, question_types_by_part, num_options_by_part)


def process_analytics_answer_dist(data, question_types_by_part, num_options_by_part):
    """
    Aggregate the analytics answer distribution data

    From the data, gets the date/time the data was last updated and reformats to the client TZ.

    Arguments:
        data: response from the analytics api
        question_types_by_part: dict of question types
        num_options_by_part: dict of number of options by question

    Returns:
        A JSON payload of:
          - data by part: an array of dicts of {value_id, correct, count} for each part_id
          - count by part: an array of dicts of:
            {
                totalFirstAttemptCount,
                totalFirstCorrectCount,
                totalFirstIncorrectCount,
                totalLastAttemptCount,
                totalLastCorrectCount,
                totalLastIncorrectCount,
            }
            for each part_id
          - last updated: string
    """
    count_by_part = {}
    data_by_part = {}
    message_by_part = {}
    num_rows_by_part = {}
    part_id_set = {
        item['part_id']
        for item in data
    }
    for item in data:
        part_id = item['part_id']
        num_rows_by_part[part_id] = num_rows_by_part.get(part_id, 0) + 1
        message = _issue_with_data(
            item,
            part_id,
            question_types_by_part,
            num_options_by_part,
            num_rows_by_part,
            part_id_set,
        )
        if message:
            message_by_part[part_id] = message
            continue
        count_by_part[part_id] = _get_part_count(item, count_by_part.get(part_id))
        data_by_part[part_id] = data_by_part.get(part_id, []) + [_get_part_data(item)]
    formatted_date_string = _format_date(data)
    response_payload = {
        'data_by_part': data_by_part,
        'count_by_part': count_by_part,
        'message_by_part': message_by_part,
        'last_update_date': formatted_date_string,
    }
    return JsonResponse(response_payload)


def _issue_with_data(item, part_id, question_types_by_part, num_options_by_part, num_rows_by_part, part_id_set):
    """
    Sanity check the data returned by the analytics API

    Arguments:
        item: current row returned by the analytics API
        part_id: the part_id of the current row
        question_types_by_part: dict of question types
        num_options_by_part: dict of number of options by question
        num_rows_by_part: dict of count of rows returned by API
        part_id_set: set of part_ids

    Returns:
        string: error message, on failure
        None: on success
    """
    message = None
    for part in part_id_set:
        if part not in question_types_by_part:
            message = _('The analytics cannot be displayed as there is an inconsistency in the data.')
            break
    else:
        if item['variant']:
            message = _('The analytics cannot be displayed for this question as randomization was set at one time.')
        elif question_types_by_part[part_id] == 'radio' and num_rows_by_part[part_id] > num_options_by_part[part_id]:
            message = _(
                'The analytics cannot be displayed for this question as the '
                'number of rows returned did not match the question definition.'
            )
        elif (
            question_types_by_part[part_id] == 'checkbox'
            and
            num_rows_by_part[part_id] > pow(2, num_options_by_part[part_id])
        ):
            message = _(
                'The analytics cannot be displayed for this question as the '
                'number of rows returned did not match the question definition.'
            )
    return message
