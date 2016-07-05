from collections import namedtuple

from weasyl.controllers import (
    admin,
    api,
    content,
    detail,
    events,
    general,
    info,
    interaction,
    messages,
    moderation,
    profile,
    settings,
    user,
    weasyl_collections,
)


Route = namedtuple('Route', ['pattern', 'name', 'view'])
"Represents a Weasyl route, to be set up by pyramid."
# TODO: Currently get/post are handled with if-blocks. One day we may want to split get/post into separate views.
# At that point, we'll have to expose a method parameter.


routes = (
    Route("/{index:(index)?}", "index", general.index_),  # 'index' is optional in the URL
    Route("/search", "search", general.search_),
    Route("/popular", "popular", general.popular_),
    Route("/streaming", "streaming", general.streaming_),
)


def setup_routes_and_views(config):
    """
    Reponsible for setting up all routes for the Weasyl application.

    Args:
        config: A pyramid Configuration for the wsgi application.
    """
    for route in routes:
        config.add_route(name=route.name, pattern=route.pattern)
        config.add_view(view=route.view, route_name=route.name)


controllers = (
    "", "weasyl.controllers.general.index_",
    "/", "weasyl.controllers.general.index_",
    "/index", "weasyl.controllers.general.index_",
    "/search", "weasyl.controllers.general.search_",
    "/popular", "weasyl.controllers.general.popular_",
    "/streaming", "weasyl.controllers.general.streaming_",

    "/signin", "weasyl.controllers.user.signin_",
    "/signin/unicode-failure", "weasyl.controllers.user.signin_unicode_failure_",
    "/signout", "weasyl.controllers.user.signout_",
    "/signup", "weasyl.controllers.user.signup_",

    "/verify/account", "weasyl.controllers.user.verify_account_",
    "/verify/premium", "weasyl.controllers.user.verify_premium_",

    "/forgotpassword", "weasyl.controllers.user.forgotpassword_",
    "/resetpassword", "weasyl.controllers.user.resetpassword_",

    "/force/resetpassword", "weasyl.controllers.user.force_resetpassword_",
    "/force/resetbirthday", "weasyl.controllers.user.force_resetbirthday_",

    "/~([^/]*)", "weasyl.controllers.profile.profile_",
    "/~([^/]+)/([^/]+)", "weasyl.controllers.profile.profile_media_",
    "/~([^/]+)/submissions?/([0-9]+)(?:/[^/.]*)?", "weasyl.controllers.detail.submission_",
    "/~([^/]+)/([^/]+)/([0-9]+)/.*", "weasyl.controllers.detail.submission_media_",
    "/user", "weasyl.controllers.profile.profile_",
    "/user/(.*)", "weasyl.controllers.profile.profile_",
    "/profile", "weasyl.controllers.profile.profile_",
    "/profile/(.*)", "weasyl.controllers.profile.profile_",
    "/submissions", "weasyl.controllers.profile.submissions_",
    "/submissions/(.*)", "weasyl.controllers.profile.submissions_",
    "/journals", "weasyl.controllers.profile.journals_",
    "/journals/(.*)", "weasyl.controllers.profile.journals_",
    "/collections", "weasyl.controllers.profile.collections_",
    "/collections/(.*)", "weasyl.controllers.profile.collections_",
    "/characters", "weasyl.controllers.profile.characters_",
    "/characters/(.*)", "weasyl.controllers.profile.characters_",
    "/shouts", "weasyl.controllers.profile.shouts_",
    "/shouts/(.*)", "weasyl.controllers.profile.shouts_",
    "/favorites", "weasyl.controllers.profile.favorites_",
    "/favorites/(.*)", "weasyl.controllers.profile.favorites_",
    "/friends", "weasyl.controllers.profile.friends_",
    "/friends/(.*)", "weasyl.controllers.profile.friends_",
    "/following", "weasyl.controllers.profile.following_",
    "/following/(.*)", "weasyl.controllers.profile.following_",
    "/followed", "weasyl.controllers.profile.followed_",
    "/followed/(.*)", "weasyl.controllers.profile.followed_",
    "/staffnotes", "weasyl.controllers.profile.staffnotes_",
    "/staffnotes/(.*)", "weasyl.controllers.profile.staffnotes_",

    "/view", "weasyl.controllers.detail.submission_",
    "/view/([0-9]*)(?:/.*)?", "weasyl.controllers.detail.submission_",
    "/submission", "weasyl.controllers.detail.submission_",
    "/submission/([0-9]*)(?:/.*)?", "weasyl.controllers.detail.submission_",
    "/submission/tag-history/([0-9]+)", "weasyl.controllers.detail.submission_tag_history_",
    "/character", "weasyl.controllers.detail.character_",
    "/character/([0-9]*)(?:/.*)?", "weasyl.controllers.detail.character_",
    "/journal", "weasyl.controllers.detail.journal_",
    "/journal/([0-9]*)(?:/.*)?", "weasyl.controllers.detail.journal_",

    "/submit", "weasyl.controllers.content.submit_",
    "/submit/visual", "weasyl.controllers.content.submit_visual_",
    "/submit/literary", "weasyl.controllers.content.submit_literary_",
    "/submit/multimedia", "weasyl.controllers.content.submit_multimedia_",
    "/submit/character", "weasyl.controllers.content.submit_character_",
    "/submit/journal", "weasyl.controllers.content.submit_journal_",
    "/submit/shout", "weasyl.controllers.content.submit_shout_",
    "/submit/comment", "weasyl.controllers.content.submit_comment_",
    "/submit/report", "weasyl.controllers.content.submit_report_",
    "/submit/tags", "weasyl.controllers.content.submit_tags_",

    "/reupload/submission", "weasyl.controllers.content.reupload_submission_",
    "/reupload/character", "weasyl.controllers.content.reupload_character_",
    "/reupload/cover", "weasyl.controllers.content.reupload_cover_",

    "/edit/submission", "weasyl.controllers.content.edit_submission_",
    "/edit/character", "weasyl.controllers.content.edit_character_",
    "/edit/journal", "weasyl.controllers.content.edit_journal_",

    "/remove/submission", "weasyl.controllers.content.remove_submission_",
    "/remove/character", "weasyl.controllers.content.remove_character_",
    "/remove/journal", "weasyl.controllers.content.remove_journal_",
    "/remove/comment", "weasyl.controllers.content.remove_comment_",

    "/frienduser", "weasyl.controllers.interaction.frienduser_",
    "/unfrienduser", "weasyl.controllers.interaction.unfrienduser_",
    "/followuser", "weasyl.controllers.interaction.followuser_",
    "/unfollowuser", "weasyl.controllers.interaction.unfollowuser_",
    "/ignoreuser", "weasyl.controllers.interaction.ignoreuser_",

    "/note", "weasyl.controllers.interaction.note_",
    "/notes", "weasyl.controllers.interaction.notes_",
    "/notes/compose", "weasyl.controllers.interaction.notes_compose_",
    "/notes/remove", "weasyl.controllers.interaction.notes_remove_",

    "/collection/offer", "weasyl.controllers.collections.collection_offer_",
    "/collection/request", "weasyl.controllers.collections.collection_request_",
    "/collection/remove", "weasyl.controllers.collections.collection_remove_",
    "/collection/acceptoffer", "weasyl.controllers.collections.collection_acceptoffer_",
    "/collection/rejectoffer", "weasyl.controllers.collections.collection_rejectoffer_",

    "/favorite", "weasyl.controllers.interaction.favorite_",

    "/messages/remove", "weasyl.controllers.messages.messages_remove_",
    "/messages/notifications", "weasyl.controllers.messages.messages_notifications_",
    "/messages/submissions", "weasyl.controllers.messages.messages_submissions_",

    "/control", "weasyl.controllers.settings.control_",
    "/settings", "weasyl.controllers.settings.control_",
    "/control/uploadavatar", "weasyl.controllers.settings.control_uploadavatar_",
    "/control/editemailpassword", "weasyl.controllers.settings.control_editemailpassword_",
    "/control/editpreferences", "weasyl.controllers.settings.control_editpreferences_",
    "/control/editprofile", "weasyl.controllers.settings.control_editprofile_",
    "/control/editcommissionprices", "weasyl.controllers.settings.control_editcommissionprices_",
    "/control/editcommishtext", "weasyl.controllers.settings.control_editcommishtext_",
    "/control/createcommishclass", "weasyl.controllers.settings.control_createcommishclass_",
    "/control/editcommishclass", "weasyl.controllers.settings.control_editcommishclass_",
    "/control/removecommishclass", "weasyl.controllers.settings.control_removecommishclass_",
    "/control/createcommishprice", "weasyl.controllers.settings.control_createcommishprice_",
    "/control/editcommishprice", "weasyl.controllers.settings.control_editcommishprice_",
    "/control/removecommishprice", "weasyl.controllers.settings.control_removecommishprice_",
    "/control/createfolder", "weasyl.controllers.settings.control_createfolder_",
    "/control/renamefolder", "weasyl.controllers.settings.control_renamefolder_",
    "/control/removefolder", "weasyl.controllers.settings.control_removefolder_",
    "/control/editfolder/([0-9]+)", "weasyl.controllers.settings.control_editfolder_",
    "/control/movefolder", "weasyl.controllers.settings.control_movefolder_",
    "/control/ignoreuser", "weasyl.controllers.settings.control_ignoreuser_",
    "/control/unignoreuser", "weasyl.controllers.settings.control_unignoreuser_",
    "/control/streaming", "weasyl.controllers.settings.control_streaming_",
    "/control/apikeys", "weasyl.controllers.settings.control_apikeys_",
    "/control/sfwtoggle", "weasyl.controllers.settings.sfwtoggle_",
    "/control/collections", "weasyl.controllers.collections.collection_options_",

    "/manage/folders", "weasyl.controllers.settings.manage_folders_",
    "/manage/following", "weasyl.controllers.settings.manage_following_",
    "/manage/friends", "weasyl.controllers.settings.manage_friends_",
    "/manage/ignore", "weasyl.controllers.settings.manage_ignore_",
    "/manage/collections", "weasyl.controllers.settings.manage_collections_",
    "/manage/thumbnail", "weasyl.controllers.settings.manage_thumbnail_",
    "/manage/tagfilters", "weasyl.controllers.settings.manage_tagfilters_",
    "/manage/avatar", "weasyl.controllers.settings.manage_avatar_",
    "/manage/banner", "weasyl.controllers.settings.manage_banner_",
    "/manage/alias", "weasyl.controllers.settings.manage_alias_",

    "/modcontrol", "weasyl.controllers.moderation.modcontrol_",
    "/modcontrol/finduser", "weasyl.controllers.moderation.modcontrol_finduser_",
    "/modcontrol/suspenduser", "weasyl.controllers.moderation.modcontrol_suspenduser_",
    "/modcontrol/report", "weasyl.controllers.moderation.modcontrol_report_",
    "/modcontrol/reports", "weasyl.controllers.moderation.modcontrol_reports_",
    "/modcontrol/closereport", "weasyl.controllers.moderation.modcontrol_closereport_",
    "/modcontrol/contentbyuser", "weasyl.controllers.moderation.modcontrol_contentbyuser_",
    "/modcontrol/hide", "weasyl.controllers.moderation.modcontrol_hide_",
    "/modcontrol/unhide", "weasyl.controllers.moderation.modcontrol_unhide_",
    "/modcontrol/manageuser", "weasyl.controllers.moderation.modcontrol_manageuser_",
    "/modcontrol/removeavatar", "weasyl.controllers.moderation.modcontrol_removeavatar_",
    "/modcontrol/removebanner", "weasyl.controllers.moderation.modcontrol_removebanner_",
    "/modcontrol/editprofiletext", "weasyl.controllers.moderation.modcontrol_editprofiletext_",
    "/modcontrol/editcatchphrase", "weasyl.controllers.moderation.modcontrol_editcatchphrase_",
    "/modcontrol/edituserconfig", "weasyl.controllers.moderation.modcontrol_edituserconfig_",
    "/modcontrol/massaction", "weasyl.controllers.moderation.modcontrol_massaction_",

    "/admincontrol", "weasyl.controllers.admin.admincontrol_",
    "/admincontrol/siteupdate", "weasyl.controllers.admin.admincontrol_siteupdate_",
    "/admincontrol/manageuser", "weasyl.controllers.admin.admincontrol_manageuser_",
    "/admincontrol/acctverifylink", "weasyl.controllers.admin.admincontrol_acctverifylink_",

    "/site-updates/([0-9]+)", "weasyl.controllers.general.site_update_",

    "/policy/tos", "weasyl.controllers.info.policy_tos_",
    "/policy/privacy", "weasyl.controllers.info.policy_privacy_",
    "/policy/copyright", "weasyl.controllers.info.policy_copyright_",
    "/policy/scoc", "weasyl.controllers.info.policy_scoc_",
    "/policy/community", "weasyl.controllers.info.policy_community_",
    "/policy/community/changes", "weasyl.controllers.info.policy_community_changes_",

    "/staff", "weasyl.controllers.info.staff_",
    "/thanks", "weasyl.controllers.info.thanks_",
    "/help", "weasyl.controllers.info.help_",
    "/help/about", "weasyl.controllers.info.help_about_",
    "/help/faq", "weasyl.controllers.info.help_faq_",
    "/help/collections", "weasyl.controllers.info.help_collections_",
    "/help/tagging", "weasyl.controllers.info.help_tagging_",
    "/help/markdown", "weasyl.controllers.info.help_markdown_",
    "/help/searching", "weasyl.controllers.info.help_searching_",
    "/help/ratings", "weasyl.controllers.info.help_ratings_",
    "/help/ratings/changes", "weasyl.controllers.info.help_ratings_changes_",
    "/help/folders", "weasyl.controllers.info.help_folders_",
    "/help/google-drive-embed", "weasyl.controllers.info.help_gdocs_",
    "/help/reports", "weasyl.controllers.info.help_reports_",

    "/api/useravatar", "weasyl.controllers.api.api_useravatar_",
    "/api/whoami", "weasyl.controllers.api.api_whoami_",
    "/api/version(\.[^.]+)?", "weasyl.controllers.api.api_version_",
    "/api/submissions/frontpage", "weasyl.controllers.api.api_frontpage_",
    "/api/submissions/([0-9]+)/view", "weasyl.controllers.api.api_submission_view_",
    "/api/journals/([0-9]+)/view", "weasyl.controllers.api.api_journal_view_",
    "/api/characters/([0-9]+)/view", "weasyl.controllers.api.api_character_view_",
    "/api/users/([^/]+)/view", "weasyl.controllers.api.api_user_view_",
    "/api/users/([^/]+)/gallery", "weasyl.controllers.api.api_user_gallery_",
    "/api/messages/submissions", "weasyl.controllers.api.api_messages_submissions_",
    "/api/messages/summary", "weasyl.controllers.api.api_messages_summary_",

    "/api/(submissions|characters|journals)/([0-9]+)/favorite", "weasyl.controllers.api.api_favorite_",
    "/api/(submissions|characters|journals)/([0-9]+)/unfavorite", "weasyl.controllers.api.api_unfavorite_",

    "/api/oauth2/authorize", "weasyl.oauth2.authorize_",
    "/api/oauth2/token", "weasyl.oauth2.token_",

    "/events/halloweasyl2014", "weasyl.controllers.events.halloweasyl2014_",
)
