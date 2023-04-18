login_schema = {
    'type': 'object',
    'properties': {
        'login': {'type': 'string'},
        'password': {'type': 'string'}
    },
    'required': ['login', 'password']
}


register_schema = {
    'type': 'object',
    'properties': {
        'login': {'type': 'string'},
        'password': {'type': 'string'},
        'first_name': {'type': 'string'},
        'second_name': {'type': 'string'}
    },
    'required': ['login', 'password', 'first_name', 'second_name']
}


profile_update_schema = {
    'type': 'object',
    'properties': {
        'first_name': {'type': 'string'},
        'second_name': {'type': 'string'}
    },
    'required': ['first_name', 'second_name']
}


conference_create_schema = {
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
    },
    'required': ['name']
}

conference_send_schema = {
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
    },
    'required': ['name']
}