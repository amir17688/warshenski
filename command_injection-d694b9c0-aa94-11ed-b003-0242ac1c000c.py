from discord_service import DiscordService
from welcome_message import WelcomeMessage
from discord_mention_factory import DiscordMentionFactory
from user_leave_notification import UserLeaveNotification

from dependency_injection import Dependencies
import json

def readJsonFile(file_name):
    with open(file_name, mode="r") as f:
        return json.load(f)

def read_secrets():
    return readJsonFile("secrets.json")

def read_config():
    return readJsonFile("config.json")

def setup_dependency_injection(config):
    return Dependencies(config)

if __name__ == "__main__":
    config = read_config()
    secrets = read_secrets()
    discord_token = secrets["discord-bot-token"]

    services = setup_dependency_injection(config)

    if config["welcome_message"]["enabled"]:
        services.welcome_message()

    if config["user_leave_notification"]["enabled"]:
        services.user_leave_notification()

    discord_service = services.discord_service()
    discord_service.run(discord_token)




    