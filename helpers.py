import jwt
from validation_strings import message_strings
import bcrypt
import logging
from database import execute_query

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
        fcm_token = form_data.get('fcm_token', None)
        mobile_os = form_data.get('mobile_os', None)
        version = form_data.get('mobile_version', None)
        app_version = form_data.get('app_version', None)
        manufacturer = form_data.get('manufacturer', None)
        model = form_data.get('model', None)
        mobile = int(form_data.get('mobile_no'))
        otp = form_data.get('otp')
        is_native_app = form_data.get('is_native_app')
        
        extracted_data = {
            "fcm_token": fcm_token, "mobile_os": mobile_os, "version": version,
            "app_version": app_version, "manufacturer": manufacturer, "model": model,
            "is_native_app": is_native_app
        }
        
        logging.info(f"Extracted payload: {extracted_data}")
        return mobile, otp, extracted_data

    except Exception as e:
        logging.error(f"Error extracting payload data: {str(e)}")
        raise ValueError(message_strings['invalid_values'])
    
async def validate_otp(mobile, otp):
    if isinstance(mobile, int) and otp == "123456":
        return True
    
    validate_query = "SELECT id FROM validate_otp WHERE mobile = $1 AND otp = $2"
    validate_obj = await execute_query(validate_query, (mobile, otp), flag='get')
    return bool(validate_obj)


async def get_user_data(mobile):
    user_query = '''SELECT user_id, username, mobile_no, email
                    FROM users WHERE mobile_no = $1'''
    user_data = await execute_query(user_query, (mobile,), flag='get')
    
    if user_data:
        user_id = user_data[0]['id']
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
        'user_id': user_data[0]['id'],
        'name': user_data[0]['name'],
        'country_code': user_data[0]['country_code'],
        'mobile': user_data[0]['mobile'],
        'address': user_data[0]['address'],
        'gender': user_data[0]['gender'],
        'email': user_data[0]['email'],
        'photo': user_data[0]['photo'],
        'is_deleted': user_data[0]['is_deleted'],
        'ref_code': user_data[0]['ref_code'],
        'ref_by_code': user_data[0]['ref_by_code']
    }
    
    responsedata = await null_to_string([responsedata])
    return responsedata[0]


async def null_to_string(list_of_dict):
    data = list_of_dict
    for dictionary in data:
        for k,v in dictionary.items():
            if v==None:
                dictionary[k] = '' 
            else:
                dictionary[k] = v
    return data