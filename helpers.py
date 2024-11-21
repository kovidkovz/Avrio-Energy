import jwt
from validation_strings import message_strings
import bcrypt
import logging
from database import execute_query
import re
import secrets

async def build_response(message: str, status, status_code, data=None):
    # Check if the status is a boolean, if not, convert it to a string
    response_status = status if isinstance(status, bool) else str(status)
    
    response = {
        'status': response_status,
        'message': str(message),
        'data'      : None
    }
    
    if data:
        response['data'] = data

    return response, status_code


async def jwt_verifier(request):
    jwt_token = request.headers.get('authorization', None)
        
    user_id = await is_valid_token(jwt_token)
    if not user_id:
        return await build_response(
            message= message_strings['invalid_token'],
            status= message_strings['status_0'],
            status_code=401  
        )
    else:
        return user_id
    
    
async def is_valid_token(token):
    try:
        print(f"Token from api is {token} and type is {type(token)}")

        token = jwt.decode(token, 'secret', algorithms=['HS256'])
        
        user_id = token.get('user_id', None)
        print(user_id)
        
        if user_id:
            return user_id
        else:
            return False
    except Exception as e:
        print(f"Error at is_valid_token as {str(str(e))}")
        return False
    

# Function to hash the password
def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt hashing algorithm.
    
    Args:
        password (str): The plain-text password to hash.
    
    Returns:
        str: The hashed password.
    """
    # Generate a salt using bcrypt
    salt = bcrypt.gensalt()
    
    # Hash the password with the salt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    # Return the hashed password as a string
    return hashed_password.decode('utf-8')


async def extract_payload_data(form_data):
    try:
        mobile = form_data.get('mobile_no')
        otp = form_data.get('otp')
        return mobile, otp

    except Exception as e:
        logging.error(f"Error extracting payload data: {str(e)}")
        raise ValueError(message_strings['invalid_values'])
    
async def validate_otp(mobile, otp):
    validate_query = "SELECT id FROM validate_otp WHERE mobile = $1 AND otp = $2"
    validate_obj = await execute_query(validate_query, (mobile, otp), flag='get')
    return bool(validate_obj)


async def get_user_data(mobile):
    user_query = '''SELECT user_id, username, mobile_no, email
                    FROM users WHERE mobile_no = $1'''
    user_data = await execute_query(user_query, (mobile,), flag='get')
    
    if user_data:
        user_id = user_data[0]['user_id']
        token = await create_token(user_id)
        return user_data, token
    return None, None


async def create_token(user_id):
    
    payload = {
        'user_id' : user_id
    }
    
    jwt_token = jwt.encode(payload, 'secret', algorithm='HS256')
    return jwt_token


async def prepare_response_data(user_data, token):
    responsedata = {
        'token': token,
        'user_id': user_data[0]['user_id'],
        'name': user_data[0]['username'],
        'mobile': user_data[0]['mobile_no'],
        'email': user_data[0]['email']
    }
    
    responsedata = await null_to_string([responsedata])
    return responsedata[0]


async def null_to_string(dict):
    data = dict
    for dictionary in data:
        for k,v in dictionary.items():
            if v==None:
                dictionary[k] = '' 
            else:
                dictionary[k] = v
    return data


async def extract_form_data(request):
    form_data = await request.form()
    form_data = await check_for_duplicate_keys(form_data)
    return form_data


async def check_for_duplicate_keys(payload):
    seen_keys = set()
    duplicates = set()

    # Iterate over the raw FormData object
    for key, value in payload.multi_items():
        if key in seen_keys:
            duplicates.add(key)
        else:
            seen_keys.add(key)

    if duplicates:
        return None
    else:
        return payload
    
async def validate_data(data, type='send'):
    # Define validation rules based on the type
    if type == 'verify':
        validation_rules = {
            'mobile_no': {
                'check': lambda value: value and validate_mob(value),
                'message': message_strings["mobile_empty"]
            },
            'otp': {
                'check': lambda value: value,
                'message': message_strings["otp_empty"]
            }
        }
    else:  # Default validation for 'send' type
        validation_rules = {
            'mobile_no': {
                'check': lambda value: value and validate_mob(value),
                'message': message_strings["mobile_empty"]
            }
        }
    
    # Initialize validation result and message
    message = ""
    try:
        validdata = True
        for key, rule in validation_rules.items():
            value = data.get(key)
            if not rule['check'](value):
                message = rule['message']
                validdata = False
                break  # Exit loop on first validation failure
        return message, validdata
    except KeyError as e:
        message = f"field required {e}"
        return message, False

        
def validate_mob(mobile):
    return True if re.findall('^[6789]\d{9}$', mobile) else False


async def otp_util(n):
    otp = ''.join(secrets.choice("0123456789") for _ in range(n))
    return otp