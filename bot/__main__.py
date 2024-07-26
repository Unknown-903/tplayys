import os
import sys
from pyrogram import filters, idle, Client, enums
from bot.config import TG_CONFIG
from bot.config import token_file, client_secrets_json
from bot.helpers.utils import find_auth_code
from bot.config import gauth
from bot.config import START_MSG
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pydrive2 import auth
from bot.services.tplay.api import TPLAY_API
from bot.helpers.utils import post_to_telegraph
import datetime
import logging
#from pyrogram import Client
#from bot.config import TG_CONFIG
LOG_FILE = 'log.txt'
#USER_SESSION_STRING_KEY = 'tringhi'

# Set up logging
logging.basicConfig(
    format="[%(asctime)s] [%(levelname)s] - %(message)s",
    datefmt="%d-%b-%y %I:%M:%S %p",
    level=logging.INFO,
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)

# Set logging level for pyrogram
logging.getLogger("pyrogram").setLevel(logging.WARNING)

LOGGER = logging.getLogger(__name__)


app = Client(
    TG_CONFIG.session,
    bot_token=TG_CONFIG.bot_token,
    api_id=TG_CONFIG.api_id,
    api_hash=TG_CONFIG.api_hash,
    sleep_threshold=30
)


try:
    if not TG_CONFIG.stringhi:
        raise KeyError("USER_SESSION_STRING is not set")
    LOGGER.info("Starting USER Session")
    USERBOT = Client(
        name="bot-user",
        session_string=TG_CONFIG.stringhi,
        no_updates=True,
    )
except KeyError as e:
    USERBOT = None
    LOGGER.warning(f"No User Session, Default Bot session will be used. Error: {e}")




@app.on_message(filters.chat(TG_CONFIG.sudo_users) & filters.command('gdrive'))
async def gdrive_helper(_, message):
    if len(message.text.split()) == 1:

        if not os.path.exists(client_secrets_json):
            await message.reply(
            "<b>No Client Secrets JSON File Found!</b>",
        )
            return

        
        if not os.path.exists(token_file):
            try:
                authurl = gauth.GetAuthUrl().replace("online", "offline")
            except auth.AuthenticationError:
                await message.reply(
                    '<b>Wrong Credentials!</b>',
                )
                return
            
            text = (
                '<b>Login In To Google Drive</b>\n<b>Send</b>`/gdrive [verification_code]`'
            )
            await message.reply(text, reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🔗 Log In URL", url=f"{authurl}")
                    ]
                ]
            ))
            return
        await message.reply(
            "<b>You're already logged in!\nTo logout type</b><code>/gdrive logout</code>",
        )
    #/gdrive logout
    elif len(message.text.split()) == 2 and message.text.split()[1] == 'logout':
        os.remove(token_file)
        await message.reply(
            '<b>You have logged out of your account!</b>',
        )
    #/gdrive [verification_code]
    elif len(message.text.split()) == 2:
        gauth.LoadCredentialsFile(token_file)
        try:
            if "localhost" in message.text.split()[1]:
                gauth.Auth(find_auth_code(message.text.split()[1]))
            else:
                gauth.Auth(message.text.split()[1])

        except auth.AuthenticationError:
            await message.reply('<b>Your Authentication code is Wrong!</b>')
            return
        gauth.SaveCredentialsFile(token_file)
        await message.reply(
            '<b>Authentication successful!</b>',
        )
    else:
        await message.reply('<b>Invaild args!</b>\nCheck <code>/gdrive</code> for usage guide')

@app.on_message(filters.chat(TG_CONFIG.sudo_users) & filters.incoming & filters.command(['webdl1']) & filters.text)
def webdl_cmd_handler(app, message):
    if len(message.text.split(" ")) <= 2:
        message.reply_text(
            "<b>Syntax: </b>`/webdl1 -c [CHANNEL SLUG] [OTHER ARGUMENTS]`")
        return
    
    command = message.text.replace("/webdl1", "").strip()
    if "-c" in command:
        from bot.services.tplay.main import TPLAY
        downloader = TPLAY(command, app, message)
        downloader.start_process()

@app.on_message(filters.command("restart1") & filters.private)
def restart_command(client, message):
    # Check if the message is from the owner
    if message.from_user.id == TG_CONFIG.owner_id:
        # Send a confirmation message to the owner
        message.reply("Restarting me babe 😘")
        # Restart the bot
        os.execl(sys.executable, sys.executable, "-m", "bot")
    else:
        message.reply("You're not my babe 😘mahesh😘 to restart the me")

@app.on_message(filters.incoming & filters.command(['start']) & filters.text)
def start_cmd_handler(app, message):
    code = "Access Denied" if message.from_user.id not in TG_CONFIG.sudo_users else "Welcome Admin"
    message.reply_text(START_MSG.format(message.from_user.username, code))


async def main():
    await app.start()
    await idle()
    await app.stop()

if __name__ == "__main__":

    # with mergeApp:
    #     bot:User = mergeApp.get_me()
    #     bot_username = bot.username

    try:
        with USERBOT:
            user = USERBOT.get_me()
            TG_CONFIG.premium = user.is_premium
        LOGGER.info("Bot boot successfully!")
    except Exception as err:
        LOGGER.error(f"{err}")
        TG_CONFIG.premium = False
        pass

    
    app.loop.run_until_complete(main())
