import os
import discord
from bot.keep_alive import keep_alive


from bot.my_bot import MyBot

super_user = ["fine4139", "ayalovex0001", "liankuma", "kujirakusu_07611", "kiyoka6639"]


bot = MyBot(intents=discord.Intents.all())

AuthB = "Bot " + os.environ['TOKEN']
headers = {"Authorization": AuthB}


keep_alive()
try:
    print("起動成功")
    bot.run(os.environ['TOKEN'])
except:
    print("起動失敗")
    os.system("kill 1")