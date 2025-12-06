"""
Brevo HTTP API Email Backend for Django

This module provides a custom email backend that sends emails via Brevo's
HTTP API instead of SMTP.

Production Safety:
    - Will NEVER crash Django on boot
    - All failures are handled gracefully with logging
    - No exceptions bubble up to crash the application
"""

import json
import logging
import base64
import re
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMessage, EmailMultiAlternatives

logger = logging.getLogger(__name__)

# Attempt to import requests, fail gracefully if not available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.error(
        "requests library is not installed. "
        "Brevo email backend will not work. Install with: pip install requests"
    )


class BrevoEmailBackend(BaseEmailBackend):
    """
    A production-safe Django email backend that sends emails using Brevo's HTTP API.
    
    Configuration:
        - BREVO_API_KEY: Your Brevo API key (required for sending)
        - DEFAULT_FROM_EMAIL: Default sender email (optional, used as fallback)
    
    Usage:
        Set in settings.py:
        EMAIL_BACKEND = 'helpers.brevo.brevo_backend.BrevoEmailBackend'
        BREVO_API_KEY = config('BREVO_API_KEY')
    
    Production Safety Guarantees:
        - Will NOT crash Django on boot if BREVO_API_KEY is missing
        - Will NOT crash if requests library is missing
        - All API errors are caught and logged
        - All network errors are caught and logged
        - All payload building errors are caught and logged
        - Returns 0 on failure, never raises exceptions in production
    """
    
    API_ENDPOINT = 'https://api.brevo.com/v3/smtp/email'
    
    def __init__(self, fail_silently=True, **kwargs):
        """
        Initialize the backend.
        
        Note: fail_silently defaults to True for production safety.
        """
        super().__init__(fail_silently=fail_silently, **kwargs)
        
        try:
            self.api_key = getattr(settings, 'BREVO_API_KEY', None)
            
            # Log warning on init if API key is missing, but don't crash
            if not self.api_key:
                logger.warning(
                    "BREVO_API_KEY is not configured. "
                    "Emails will not be sent until the API key is set."
                )
        except Exception as e:
            logger.error(f"Error initializing BrevoEmailBackend: {e}")
            self.api_key = None
    
    def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects and return the number of email
        messages sent.
        
        This method is production-safe and will never raise exceptions.
        """
        try:
            if not email_messages:
                return 0
            
            # Check if requests library is available
            if not REQUESTS_AVAILABLE:
                logger.error(
                    "Cannot send emails: requests library is not installed."
                )
                return 0
            
            # Check API key at send time (graceful failure, not boot crash)
            if not self.api_key:
                logger.error(
                    "BREVO_API_KEY is not configured. "
                    "Cannot send emails via Brevo HTTP API."
                )
                return 0
            
            num_sent = 0
            for message in email_messages:
                try:
                    if self._send(message):
                        num_sent += 1
                except Exception as e:
                    logger.error(
                        f"Failed to send email via Brevo API: {e}",
                        exc_info=True
                    )
                    # Continue to next message, don't stop the loop
            
            return num_sent
            
        except Exception as e:
            logger.error(
                f"Unexpected error in send_messages: {e}",
                exc_info=True
            )
            return 0
    
    def _send(self, message):
        """
        Send a single EmailMessage via Brevo API.
        
        Returns True if the email was sent successfully, False otherwise.
        Never raises exceptions.
        """
        try:
            # Build the API payload
            payload = self._build_payload(message)
            
            if payload is None:
                logger.error("Failed to build email payload")
                return False
            
            # Make the API request
            headers = {
                'api-key': self.api_key,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
            
            response = requests.post(
                self.API_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code in (200, 201):
                try:
                    message_id = response.json().get('messageId', 'unknown')
                except Exception:
                    message_id = 'unknown'
                    
                logger.info(
                    f"Email sent successfully via Brevo API: "
                    f"to={message.to}, messageId={message_id}"
                )
                return True
            else:
                logger.error(
                    f"Brevo API error: status={response.status_code}, "
                    f"response={response.text[:500]}"
                )
                return False
                
        except requests.Timeout:
            logger.error("Brevo API request timed out")
            return False
        except requests.ConnectionError:
            logger.error("Brevo API connection error - network issue")
            return False
        except requests.RequestException as e:
            logger.error(f"Brevo API request failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}", exc_info=True)
            return False
    
    def _build_payload(self, message):
        """
        Build the Brevo API payload from a Django EmailMessage.
        
        Returns None if payload cannot be built.
        """
        try:
            # Parse sender
            from_email = message.from_email or getattr(
                settings, 'DEFAULT_FROM_EMAIL', 'admin@devmate.space'
            )
            sender_name, sender_email = self._parse_email(from_email)
            
            # Validate required fields
            if not message.to:
                logger.error("Email has no recipients")
                return None
            
            if not message.subject and not message.body:
                logger.error("Email has no subject or body")
                return None
            
            payload = {
                'sender': {
                    'email': sender_email,
                },
                'to': [self._format_recipient(r) for r in message.to],
                'subject': message.subject or '(No Subject)',
            }
            
            # Add sender name if present
            if sender_name:
                payload['sender']['name'] = sender_name
            
            # Handle HTML and plain text content
            if isinstance(message, EmailMultiAlternatives):
                # Check for HTML alternative
                for content, mimetype in getattr(message, 'alternatives', []):
                    if mimetype == 'text/html':
                        payload['htmlContent'] = content
                        break
                # Also include plain text if available
                if message.body:
                    payload['textContent'] = message.body
            elif getattr(message, 'content_subtype', 'plain') == 'html':
                payload['htmlContent'] = message.body
            else:
                payload['textContent'] = message.body or ''
            
            # Ensure we have some content
            if 'htmlContent' not in payload and 'textContent' not in payload:
                payload['textContent'] = ''
            
            # Add CC recipients
            if getattr(message, 'cc', None):
                payload['cc'] = [self._format_recipient(r) for r in message.cc]
            
            # Add BCC recipients
            if getattr(message, 'bcc', None):
                payload['bcc'] = [self._format_recipient(r) for r in message.bcc]
            
            # Add Reply-To
            if getattr(message, 'reply_to', None):
                try:
                    reply_to_name, reply_to_email = self._parse_email(message.reply_to[0])
                    payload['replyTo'] = {'email': reply_to_email}
                    if reply_to_name:
                        payload['replyTo']['name'] = reply_to_name
                except (IndexError, TypeError):
                    pass  # Skip if reply_to is malformed
            
            # Handle attachments
            if getattr(message, 'attachments', None):
                payload['attachment'] = []
                for attachment in message.attachments:
                    try:
                        if isinstance(attachment, tuple) and len(attachment) >= 2:
                            filename = attachment[0]
                            content = attachment[1]
                            if isinstance(content, bytes):
                                content = base64.b64encode(content).decode('utf-8')
                            elif isinstance(content, str):
                                content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
                            payload['attachment'].append({
                                'name': filename,
                                'content': content,
                            })
                    except Exception as e:
                        logger.warning(f"Failed to process attachment: {e}")
                        continue  # Skip this attachment, continue with others
            
            return payload
            
        except Exception as e:
            logger.error(f"Error building email payload: {e}", exc_info=True)
            return None
    
    def _parse_email(self, email_string):
        """
        Parse an email string that may contain a name.
        e.g., "John Doe <john@example.com>" -> ("John Doe", "john@example.com")
             "john@example.com" -> (None, "john@example.com")
        
        Returns (None, email_string) if parsing fails.
        """
        try:
            if not email_string:
                return None, 'admin@devmate.space'
            
            email_string = str(email_string).strip()
            match = re.match(r'^(.+?)\s*<(.+?)>$', email_string)
            if match:
                return match.group(1).strip(), match.group(2).strip()
            return None, email_string
        except Exception:
            return None, str(email_string) if email_string else 'admin@devmate.space'
    
    def _format_recipient(self, email_string):
        """
        Format a recipient email for the Brevo API.
        
        Returns a dict with 'email' key, and optionally 'name'.
        """
        try:
            name, email = self._parse_email(email_string)
            recipient = {'email': email}
            if name:
                recipient['name'] = name
            return recipient
        except Exception:
            return {'email': str(email_string) if email_string else 'unknown@example.com'}
