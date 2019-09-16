from copy import copy
import re

from django.utils.log import AdminEmailHandler
from django.views.debug import ExceptionReporter


class StanfordAdminEmailHandler(AdminEmailHandler):
    def emit(self, record):
        try:
            request = record.request
            message = record.getMessage()
            pathname = requeust['RAW_URI']
            match = re.match(r"(?P<path>/courses/(course-v1:[^/]+|[^/]+/[^/]+/[^/]+))", pathname)
            if match:
                pathname = match.group('path')
            # ERROR lagunita.stanford.edu/auth/login
            # ERROR lagunita.stanford.edu/courses/course-v1:HumanitiesSciences+Econ1V+Summer2019
            subject = "{level} {host}/{path}".format(
                level=record.levelname,
                host=request['HTTP_HOST'],
                path=pathname,
            )
        except Exception:
            subject = '%s: %s' % (
                record.levelname,
                record.getMessage()
            )
            request = None
        subject = self.format_subject(subject)

        # Since we add a nicely formatted traceback on our own, create a copy
        # of the log record without the exception data.
        no_exc_record = copy(record)
        no_exc_record.exc_info = None
        no_exc_record.exc_text = None

        if record.exc_info:
            exc_info = record.exc_info
        else:
            exc_info = (None, record.getMessage(), None)

        reporter = ExceptionReporter(request, is_email=True, *exc_info)
        message = "%s\n\n%s" % (self.format(no_exc_record), reporter.get_traceback_text())
        html_message = reporter.get_traceback_html() if self.include_html else None
        self.send_mail(subject, message, fail_silently=True, html_message=html_message)
