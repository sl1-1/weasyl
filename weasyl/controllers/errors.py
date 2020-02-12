from __future__ import absolute_import

from pyramid.view import view_config

from libweasyl.exceptions import ExpectedWeasylError

from weasyl.error import UnverifiedUser


@view_config(context=ExpectedWeasylError, renderer='/error/expected.jinja2')
def expected_error(exc, request):
    if isinstance(exc[0], str):
        return {'error': exc[0]}
    if isinstance(exc[0], tuple):
        return {'error': exc[0][0], 'links': exc[0][1]}


@view_config(context=UnverifiedUser, renderer='/error/unverified.jinja2')
def expected_error(exc, request):
    request.response.status = 403
    return {'error': exc[0][0], 'links': exc[0][1]}
