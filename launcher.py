from bot import bot
from os import getenv
from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv()
    bot.run(getenv('BOT_TOKEN'))
