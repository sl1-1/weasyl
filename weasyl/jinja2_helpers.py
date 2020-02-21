import urllib

import arrow
import pyramid_jinja2.filters
from jinja2 import Markup, contextfilter
from pyramid.threadlocal import get_current_request
from pyramid.traversal import PATH_SAFE

from libweasyl import text, staff, ratings
from libweasyl.legacy import get_sysname

from weasyl import define, macro


def sfw():
    mode = get_current_request().cookies.get('sfwmode', 'nsfw')
    if mode == 'nsfw':
        return False
    else:
        return True


@contextfilter
def route_path_filter(ctx, route_name, *elements, **kw):
    url = pyramid_jinja2.filters.route_path_filter(ctx, route_name, *elements, **kw)

    # Fixes urls returned from pyramids route_path so that that tildes are not url quoted.
    url = urllib.quote(urllib.unquote(url), safe=PATH_SAFE)

    return url


jinja2_globals = {
    "arrow": arrow,
    "CAPTCHA": define._captcha_public,
    'THUMB': define.thumb_for_sub,
    'WEBP_THUMB': define.webp_thumb_for_sub,
    'USER_TYPE': define.user_type,
    'TOKEN': define.get_token,
    'staff': staff,
    'R': ratings,
    "QUERY_STRING": define.query_string,
    'sfw': sfw,
    "LOCAL_ARROW": define.local_arrow,
    "SYMBOL": define.text_price_symbol,
    'M': macro,
    'SHA': define.CURRENT_SHA,
    "NOW": define.get_time,
}

filters = {
    'LOGIN': get_sysname,
    'DATE': define.convert_date,
    'TIME': define._convert_time,
    'MARKDOWN': lambda x: Markup(text.markdown(x)),
    'MARKDOWN_EXCERPT': lambda x: Markup(text.markdown_excerpt(x)),
    'SLUG': text.slug_for,
    'route_path': route_path_filter,
}
