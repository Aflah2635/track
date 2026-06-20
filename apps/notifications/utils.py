import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import EmailLog
from apps.audit.utils import log_to_discord, LogEvents, LogColors

logger = logging.getLogger(__name__)

def send_tracked_email(email_type, subject, template_name, context, recipient_list, user=None):
    """
    Sends an HTML email with a text fallback and logs the outcome in EmailLog.
    """
    if isinstance(recipient_list, str):
        recipient_list = [recipient_list]

    html_content = render_to_string(f"emails/{template_name}.html", context)
    text_content = render_to_string(f"emails/{template_name}.txt", context)

    status = 'SENT'
    error_message = ''

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except Exception as e:
        status = 'FAILED'
        error_message = str(e)
        logger.error(f"Failed to send {email_type} email to {recipient_list}: {e}")

    # Log each recipient separately
    for recipient in recipient_list:
        EmailLog.objects.create(
            user=user,
            email_type=email_type,
            recipient=recipient,
            subject=subject,
            status=status,
            error_message=error_message
        )
        
        # Send Discord Notification specifically for Password Resets
        if email_type == 'PASSWORD_RESET':
            if status == 'SENT':
                log_to_discord(
                    event_type=LogEvents.PASSWORD_RESET_REQUESTED,
                    title="Password Reset Email Sent",
                    user=user or recipient,
                    details={"Recipient": recipient, "Status": "Success"},
                    color=LogColors.SUCCESS,
                    emoji="📩"
                )
            else:
                log_to_discord(
                    event_type=LogEvents.PASSWORD_RESET_REQUESTED,
                    title="Password Reset Email Failed",
                    user=user or recipient,
                    details={"Recipient": recipient, "Status": "Failed", "Error": error_message},
                    color=LogColors.ERROR,
                    emoji="🚨"
                )

    return status == 'SENT'
