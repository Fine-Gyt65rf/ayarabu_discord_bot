import os
import re
import discord
from bot.keep_alive import keep_alive

from discord.ext import commands

from ui.meow_translator import MeowTalk


class memberListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spread_content = self.bot.spread_content
        self.mongo_db = self.bot.mongo_db

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # "general" というテキストチャンネルを取得して
        # 新規参加者に対してメッセージを送信
        channel = discord.utils.get(member.guild.text_channels, name="雑談")
        if channel is not None:
            await channel.send(f"ようこそ {member.mention} さん！サーバーへ参加ありがとうございます。\
                               \nこのサーバーでは、みんなで楽しく交流しながら同盟戦を盛り上げています！\
                               \n🔹 サーバーでできること\
                               \n・同盟戦の作戦会議＆情報共有 \
                               \n・雑談＆ゲームの話\
                               \n・戦力報告も自動で行えます！\
                               \n🔹 まずはここをチェック！\
                               \n✅ #雑談：気軽に話しかけてみてください！相談もOKです！\
                               \n✅ #レシピ交易所：レシピの譲渡や交換の相談などを行っています！\
                               \n✅ #タイムライン相談室：タイムラインの相談などを行っています！\
                               \n✅ #戦力登録専用(ほっこり茶屋の方のみ)：ぜひとも自分の戦力を書いてみてください！例えば、「対闇lv300 3p」のように戦力を書いてみてください")
            #self.spread_content.registered_name()
        else:
            print(f"{member.name} さんが参加しましたが、メッセージを送るチャンネルが見つかりませんでした。")