# https://stackoverflow.com/questions/714063/importing-modules-from-parent-folder
import os
import sys
import inspect

currentdir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from QA import QA
import discord as dsc
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = dsc.Client()
qa = QA()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    await message.channel.send(qa.responder_pregunta(message.content))

client.run(TOKEN)