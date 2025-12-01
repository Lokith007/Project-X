from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re


class MinimumLengthSpecialCharValidator:
    """
    Validate that the password contains:
    - At least 8 characters
    - At least one special character
    """
    
    def validate(self, password, user=None):
        # Check minimum length
        if len(password) < 8:
            raise ValidationError(
                _("Password must contain at least 8 characters."),
                code='password_too_short',
            )
        
        # Check for at least one special character
        special_chars = r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/~`]'
        if not re.search(special_chars, password):
            raise ValidationError(
                _("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>_-+=[]\\;/~`)."),
                code='password_no_special',
            )
    
    def get_help_text(self):
        return _(
            "Your password must contain at least 8 characters and at least one special character."
        )
