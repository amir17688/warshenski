from flask import Blueprint, request
from modules.MessagesManager.api.functions import db_getMessage, db_sendMessage

messages_module = Blueprint('messages', __name__)

@messages_module.route('/message/send')
def send_message():
    if request.method == 'PUT':
        return db_sendMessage(request.get_json())


@messages_module.route('/messages/<int:dialog_id>')
def get_message(dialog_id):
    if request.method == 'GET':
        return db_getMessage(dialog_id)


@messages_module.route('/messages')
def get_message(dialog_id):
    if request.method == 'GET':
        return db_getMessage(dialog_id)