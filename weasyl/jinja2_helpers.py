from jinja2 import Markup
from jinja2 import evalcontextfilter
from libweasyl import text, staff, ratings
from libweasyl.legacy import get_sysname
from libweasyl.models.users import Login

import arrow

from pyramid.threadlocal import get_current_request

import define, macro


# "STR": str,
#                 "PRICE": text_price_amount,
#                 "MARKDOWN_EXCERPT": text.markdown_excerpt,
#                 "SUMMARIZE": summarize,

#                 "INLINE_JSON": html.inline_json,
#                 "constants": libweasyl.constants,
#                 "getattr": getattr,
#                 "json": json,
#                 "sorted": sorted,
#                 "request": the_fake_request,
#                 "resource_path": get_resource_path,

@evalcontextfilter
def LOGIN(eval_ctx, username):
    return get_sysname(username)


@evalcontextfilter
def DATE(eval_ctx, unixtime):
    return define.convert_date(unixtime)


@evalcontextfilter
def TIME(eval_ctx, unixtime):
    return define._convert_time(unixtime)


@evalcontextfilter
def CDNIFY(eval_ctx, url):
    return define.cdnify_url(url)


@evalcontextfilter
def MARKDOWN(eval_ctx, markdown):
    return Markup(text.markdown(markdown))


@evalcontextfilter
def MARKDOWN_EXCERPT(eval_ctx, markdown):
    return Markup(text.markdown_excerpt(markdown))


@evalcontextfilter
def SLUG(eval_ctx, title):
    return text.slug_for(title)


def _render(*args, **kwargs):
    # TODO: This goes away once all templates are converted.
    return Markup(define.render(*args, **kwargs))


def msg_submissions():
    request = get_current_request()
    return define._page_header_info(request.userid)[3]


def msg_comments():
    request = get_current_request()
    return define._page_header_info(request.userid)[1]


def msg_notifications():
    request = get_current_request()
    return define._page_header_info(request.userid)[2]


def msg_journals():
    request = get_current_request()
    return define._page_header_info(request.userid)[4]


def msg_notes():
    request = get_current_request()
    return define._page_header_info(request.userid)[0]


def sfw():
    mode = get_current_request().cookies.get('sfwmode', 'nsfw')
    if mode == 'nsfw':
        return False
    else:
        return True


def User():
    request = get_current_request()
    return request.pg_connection.query(Login).filter(Login.userid == request.userid).one_or_none()


def path_for(obj, operation='view'):
    request = get_current_request()
    # TODO: Figure out why we get a double / here
    return obj.canonical_path(request, operation)[1:]


jinja2_globals = {
    "arrow": arrow,
    "CAPTCHA": define._captcha_public,
    'THUMB': define.thumb_for_sub,
    'WEBP_THUMB': define.webp_thumb_for_sub,
    'USER_TYPE': define.user_type,
    'PATH': define._get_path,
    'TOKEN': define.get_token,
    'staff': staff,
    'R': ratings,
    "QUERY_STRING": define.query_string,
    'RENDER': _render,
    'id_fields': {
        'submit': 'submitid',
        'char': 'charid',
        'journal': 'journalid',
        'user': 'userid',
    },
    'sfw': sfw,
    'msg_submissions': msg_submissions,
    'msg_comments': msg_comments,
    'msg_notifications': msg_notifications,
    'msg_journals': msg_journals,
    'msg_notes': msg_notes,
    "LOCAL_ARROW": define.local_arrow,
    'path_for': path_for,
    "SYMBOL": define.text_price_symbol,
    'M': macro,
    'SHA': define.CURRENT_SHA,
    "NOW": define.get_time,
    "resource_path": define.get_resource_path,
}

filters = {
    'LOGIN': LOGIN,
    'DATE': DATE,
    'TIME': TIME,
    'CDNIFY': CDNIFY,
    'MARKDOWN': MARKDOWN,
    'MARKDOWN_EXCERPT': MARKDOWN_EXCERPT,
    'SLUG': SLUG
}


