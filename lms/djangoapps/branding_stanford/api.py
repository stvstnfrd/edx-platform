from django.conf import settings
from django.utils.translation import ugettext as _

from branding import api


old_get_footer = api.get_footer


def get_footer(is_secure=True):
    footer = old_get_footer(is_secure)
    footer = _patch_copyright(footer)
    footer = _patch_external_courses_link(footer)
    return footer


def _patch_copyright(footer):
    text = settings.FOOTER_DISCLAIMER_TEXT
    if text is not None:
        footer['copyright'] = _(text)
    return footer


def _patch_external_courses_link(footer):
    link = settings.FOOTER_EXTERNAL_COURSES_LINK
    if link is not None:
        url = link['url']
        text = link['text']
        text = _(text)
        footer.update({
            'edx_org_link': {
                'text': text,
                'url': url,
            },
        })
    return footer


def patch():
    api.get_footer = get_footer
