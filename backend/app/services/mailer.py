"""Mock email delivery.

In production, replace ``send_password_reset`` with an SMTP/transactional
provider. For this project, emails are written to the application log (and the
dev-only reset token is surfaced in the API response when SMTP is disabled).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def send_password_reset(email: str, reset_link: str) -> None:
    logger.info(
        "MOCK EMAIL -> to=%s subject='RainMumbai AI password reset' "
        "body='Reset your password here: %s'",
        email,
        reset_link,
    )
