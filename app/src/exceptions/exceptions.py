from dataclasses import dataclass

class AccessDeniedException(Exception):
    pass

@dataclass(frozen=True)
class ReturnMessages:
    user_exists: str = "Account already exists"
    user_created: str = "User successfully created. Check your email for confirmation."
    user_logout: str = "Successfully logged out"
    user_banned: str = "User is banned"
    verification_error: str = "Verification error"
    credentials_error: str = "Could not validate credentials"
    email_confirmed: str = "Email confirmed"
    email_not_confirmed: str = "Email not confirmed"
    email_already_confirmed: str = "Your email is already confirmed"
    emaii_check_confirmation: str = "Check your email for confirmation."
    email_invalid: str = "Invalid email"
    password_invalid: str = "Invalid password"
    token_invalid: str = "Invalid token"
    token_refresh_invalid: str = "Invalid refresh token"
    token_email_invalid: str = "Invalid token for email verification"
    token_scope_wrong: str = "Invalid scope for token"

    record_not_found: str = "Record not found"
    access_forbiden: str = "Access forbidden"
    operation_forbiden: str = "Operation forbidden"


RETURN_MSG = ReturnMessages()

