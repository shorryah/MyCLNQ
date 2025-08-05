import re
from datetime import date
import phonenumbers

def is_valid_name(name: str) -> bool:
    return 2 < len(name) <= 70

def is_valid_email_format(email: str) -> bool:
    regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(regex, email) is not None

def is_valid_phone(phone: str, country_code: str) -> bool:
    try:
        if not country_code.startswith("+"):
            return False
        full_number = country_code + phone
        parsed_number = phonenumbers.parse(full_number, None)
        return phonenumbers.is_valid_number(parsed_number)
    except Exception:
        return False

def is_valid_password(pw: str) -> bool:
    regex = r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{9,}$"
    return re.match(regex, pw) is not None

def passwords_match(password: str, confirm_password: str) -> bool:
    return password == confirm_password

def is_valid_gender(gender: str) -> bool:
    return gender.lower() in ['male', 'female', 'prefer not to say']

# def is_valid_id_type(id_type: str) -> bool:
#     allowed = ["NRIC", "PASSPORT", "DRIVING LICENSE", "AADHAAR", "KTP", "EMIRATES", "CPR"]
#     return id_type.upper() in allowed

def is_valid_dob(dateOfBirth: date) -> bool:
    today = date.today()
    return dateOfBirth <= today


def validate_user_data(user_data):
    errors = []
    if not is_valid_name(user_data.firstName):
        errors.append("First name must be 3-70 characters.")
    if not is_valid_name(user_data.lastName):
        errors.append("Last name must be 3-70 characters.")
    if not is_valid_phone(user_data.phoneNumber, user_data.countryCode):
        errors.append("Invalid phone number for the specified country code.")
    if not is_valid_email_format(user_data.email):
        errors.append("Invalid email format.")
    if not is_valid_dob(user_data.dateOfBirth):
        errors.append("Invalid date of birth.")
    if not is_valid_gender(user_data.gender):
        errors.append("Invalid gender choice. Please type either 'male', 'female' or 'prefer not to say'.")
    # if not is_valid_id_type(user_data.id_type):
    #     errors.append("Invalid user identification type. Please type either NRIC, PASSPORT, DRIVING LICENSE, AADHAAR, KTP, EMIRATES or CPR.")
    if not is_valid_password(user_data.password):
        errors.append("Password must have 9+ characters, with uppercase, number, and special character.")
    if not passwords_match(user_data.password, user_data.confirm_password):
        errors.append("Passwords do not match.")
    return errors
