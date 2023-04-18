from flask import Blueprint, request, redirect, jsonify, abort
from modules.ProfileManager.api.db_methods import db_isAuthDataValid, db_addProfile, db_getProfileInfo, db_getUserID, \
    db_setLastVisit
from modules.ProfileManager.api.db_methods import db_isProfileExists
from modules.SessionControl.app import initRedis_db, generateSession
# from flask_expects_json import expects_json
from hashlib import sha256
from modules.json_schemas import login_schema, register_schema
import jsonschema
import json

auth_module = Blueprint('auth', __name__)


@auth_module.route('/register', methods=['GET', 'POST'])
def hRegister():
    if request.method == 'POST':
        try:
            data = json.loads(request.data)
            jsonschema.validate(data, register_schema)
        except (jsonschema.exceptions.ValidationError, json.decoder.JSONDecodeError):
            return {'status': -1, 'message': 'Найдены ошибки в JSON\'е'}

        if not data:
            return jsonify({'status': 0, 'message': 'Требуется запрос с JSON\'ом'})

        if not data['login'].isalpha():
            return jsonify({'status': 0, 'message': 'Поле \'логин\' должно состоять только из букв формата [a-Z]'})

        if not data['login'] or not data['password'] or not data['first_name'] or not data['second_name']:
            return jsonify({'status': 0, 'message': 'Заполнены не все данные'})

        data.update({'password': sha256(data['password'].encode()).hexdigest()})

        if db_isProfileExists(data):
            return jsonify({'status': 0, 'message': 'Аккаунт с таким логином уже зарегистрирован'})

        return jsonify(db_addProfile(data))


@auth_module.route('/', methods=['GET', 'POST'])
@auth_module.route('/login', methods=['GET', 'POST'])
def hLogin():
    r = initRedis_db()
    if request.method == 'POST':
        try:
            data = json.loads(request.data)
            jsonschema.validate(data, login_schema)
        except (jsonschema.exceptions.ValidationError, json.decoder.JSONDecodeError):
            return {'status': -1, 'message': 'Найдены ошибки в запросе'}

        if not data:
            return jsonify({'status': 0, 'message': 'Требуется запрос с JSON\'ом'})

        if not data['login'] or not data['password']:
            return jsonify({'status': 0, 'message': 'Заполнены не все данные'})

        if not data['login'].isalpha():
            return jsonify({'status': 0, 'message': 'Поле \'логин\' должно состоять только из букв формата [a-Z]'})

        data.update({'password': sha256(data['password'].encode()).hexdigest()})

        if not db_isAuthDataValid(data):
            return jsonify({'status': 0, 'message': 'Неправильный логин/пароль'})

        user_id = db_getUserID(data)
        if db_getProfileInfo(user_id)['is_blocked']:
            return jsonify({'status': 0, 'message': 'Аккаунт заблокирован'})

        db_setLastVisit(user_id)
        generateSession(user_id, r)
        return jsonify(db_getProfileInfo(user_id))


# TODO: Сделать валидацию JSON'а от пользователя
@auth_module.route('/logout', methods=['GET', 'POST'])
def logout():
    try:
        data = json.loads(request.data)
        jsonschema.validate(data, login_schema)
    except (jsonschema.exceptions.ValidationError, json.decoder.JSONDecodeError):
        return {'status': -1, 'message': 'Найдены ошибки в запросе'}

    r = initRedis_db()
    r.delete(db_getUserID(data))
    return jsonify({'status': 1})


# TODO: Сделать валидацию JSON'а от пользователя
@auth_module.route('/reset-password/', methods=['GET', 'POST'])
def hResetPW():
    r = initRedis_db()
    if request.method == 'POST':
        data = json.loads(request.data)
        r.delete(db_getUserID(data))
        # data.update({'password': sha256(data['password'].encode())})  # Хешируем введённый пользователем пароль
        return redirect('index')
