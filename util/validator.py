import re


email_regex = re.compile(r"^[-!#$%&'*+/0-9=?A-Z^_a-z{|}~](\.?[-!#$%&'*+/0-9=?A-Z^_a-z{|}~])*@[a-zA-Z](-?[a-zA-Z0-9])*(\.[a-zA-Z](-?[a-zA-Z0-9])*)+$")


def is_valid_email(email: str) -> bool:
    if email_regex.match(email):
        return True
    return False
