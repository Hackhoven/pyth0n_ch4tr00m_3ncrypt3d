import hashlib
import secrets

def generate_secure_id(prefix=''):
    # Generate a secure ID by combining a random token with an optional prefix

    random_token = secrets.token_hex(16)
    combined_id = prefix + random_token
    return hashlib.sha256(combined_id.encode('utf-8')).hexdigest()

def generate_secure_user_id():
    return generate_secure_id('user')

def generate_secure_chat_id():
    return generate_secure_id('chat')

def find_id_by_name(desired_name, data):

    # Find an ID by a given name in a dictionary of data
    for name_id, name in data.items():
        if name == desired_name:
            return name_id
    return None
