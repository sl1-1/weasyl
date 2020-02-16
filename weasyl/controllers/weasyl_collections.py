from __future__ import absolute_import

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import view_config

from weasyl import define, collection, profile
from weasyl.error import WeasylError
from weasyl.controllers.decorators import login_required, token_checked


@view_config(route_name="collection_options", renderer='/manage/collection_options.jinja2', request_method='GET')
@login_required
def collection_options_get_(request):
    jsonb_settings = define.get_profile_settings(request.userid)
    form_settings = {
        "allow_request": jsonb_settings.allow_collection_requests,
        "allow_notification": jsonb_settings.allow_collection_notifs,
    }
    return {'settings': form_settings, 'title': "Collection Options"}


@view_config(route_name="collection_options", renderer='/manage/collection_options.jinja2', request_method='POST')
@login_required
@token_checked
def collection_options_post_(request):
    form = request.web_input(allow_request="", allow_notification="")

    jsonb_settings = define.get_profile_settings(request.userid)
    jsonb_settings.allow_collection_requests = form.allow_request
    jsonb_settings.allow_collection_notifs = form.allow_notification

    profile.edit_preferences(request.userid, jsonb_settings=jsonb_settings)
    raise HTTPSeeOther(location="/control")


@view_config(route_name="collection_offer", renderer='/manage/collection_offer_request.jinja2', request_method="POST")
@login_required
@token_checked
def collection_offer_(request):
    form = request.web_input(submitid="", username="")
    form.otherid = profile.resolve(None, None, form.username)
    form.submitid = int(form.submitid)

    if not form.otherid:
        raise WeasylError("userRecordMissing")
    if request.userid == form.otherid:
        raise WeasylError("cannotSelfCollect")

    collection.offer(request.userid, form.submitid, form.otherid)
    return {'message': "**Success!** Your collection offer has been sent "
                       "and the recipient may now add this submission to their gallery.",
            'submission': form.submitid
            }


@view_config(route_name="collection_request", renderer='/manage/collection_offer_request.jinja2', request_method="POST")
@login_required
@token_checked
def collection_request_(request):
    if not define.is_vouched_for(request.userid):
        raise WeasylError("vouchRequired")

    form = request.web_input(submitid="")
    form.submitid = int(form.submitid)
    form.otherid = define.get_ownerid(submitid=form.submitid)

    if not form.otherid:
        raise WeasylError("userRecordMissing")
    if request.userid == form.otherid:
        raise WeasylError("cannotSelfCollect")

    collection.request(request.userid, form.submitid, form.otherid)
    return {'message': "**Success!** Your collection request has been sent. "
                       "The submission author may approve or reject this request.",
            'submission': form.submitid
            }


@view_config(route_name="collection_remove", request_method="POST")
@login_required
@token_checked
def collection_remove_(request):
    form = request.web_input(submissions=[])
    # submissions input format: "submissionID;collectorID"
    submissions = [int(x.split(";")[0]) for x in form.submissions]

    collection.remove(request.userid, submissions)
    raise HTTPSeeOther(location="/manage/collections")
