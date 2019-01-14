from django.conf import settings
from django.utils.translation import ugettext_noop as _

import logging
logger = logging.getLogger(__name__)


def create_notice_types(sender, **kwargs):
    if "pinax.notifications" in settings.INSTALLED_APPS:
        from pinax.notifications.models import NoticeType
        logger.debug("Creating notices for myapp")
        NoticeType.create("vatic_job_invite", _("Space-Time Job Invitation Received"), _("you have received an invitation"))
        NoticeType.create("vatic_job_accept", _("Space-Time Job Acceptance Received"), _("an invitation you sent has been accepted"))
    else:
        logger.debug("Skipping creation of NoticeTypes as notification app not found")