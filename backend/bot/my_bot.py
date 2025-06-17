
import discord
from bot.keep_alive import keep_alive

from discord.ext import commands

from bson import ObjectId

from core.spreadsheet_operator import SpreadContent
from core.mongodb_operator import MongoDB
from ui.meow_translator import MeowTalk
from listener.member_listener import memberListener
from listener.message_listener import messageListener

class MyBot(commands.Bot):

    def __init__(self, command_prefix='!', *args, **kwargs):
        super().__init__(command_prefix, *args, **kwargs)
        self.spread_content = SpreadContent()
        self.mongo_db = MongoDB()

    async def on_ready(self):
        print(f'ログインしました: {self.user}')
        
    
    async def setup_hook(self):
        # Botが起動する際に、Cogをロード
        await self.add_cog(messageListener(self))
        await self.add_cog(memberListener(self))

    def list_members(self, guild_id):
        """指定サーバー内のメンバー情報（名前、ID、ロール）を表示"""
        guild = self.get_guild(guild_id)  # 特定のサーバーを取得

        if guild is None:
            print("指定されたサーバーが見つかりません。")
            return

        members_info = []
        member_roles_list={}
        for member in guild.members:
            roles = [role.name for role in member.roles if role.name != "@everyone"]
            member_roles_list[str(member)]=roles
            member_info = f"名前: {member.display_name}, ID: {member.id}, ユーザー名: {str(member)}, ロール: {', '.join(roles) or 'なし'}"
            members_info.append(member_info)
        
        # メンバー情報をコンソールに表示
        # print(f"サーバー: {guild.name} のメンバー情報\n" + "\n".join(members_info))

        return member_roles_list


    async def add_role(self, guild_id: int, member_user_name: str, role_name: str):
        """指定サーバー内の特定のメンバーにロールを付与"""
        guild = self.get_guild(guild_id)

        if guild is None:
            print("指定されたサーバーが見つかりません。")
            return

        member = guild.get_member_named(member_user_name)
        role = discord.utils.get(guild.roles, name=role_name)

        if member is None:
            print("指定されたIDのメンバーが見つかりません。\n")
            return "指定されたIDのメンバーが見つかりません。\n"
        if role is None:
            print("指定された名前のロールが見つかりません。\n")
            return "指定された名前のロールが見つかりません。\n"

        if role not in member.roles:
            await member.add_roles(role)
            print(f"{member.display_name} にロール {role.name} を付与しました。\n")
            return f"{member.display_name} にロール {role.name} を付与しました。\n"
        else:
            print(f"{member.display_name} は既にロール {role.name} を持っています。\n")
            return f"{member.display_name} は既にロール {role.name} を持っています。\n"

    async def delete_role(self, guild_id: int, member_user_name: str, role_name: str):
        """指定サーバー内の特定のメンバーからロールを削除"""
        guild = self.get_guild(guild_id)

        if guild is None:
            print("指定されたサーバーが見つかりません。")
            return "指定されたサーバーが見つかりません。"

        member = guild.get_member_named(member_user_name)
        role = discord.utils.get(guild.roles, name=role_name)

        if member is None:
            print("指定されたIDのメンバーが見つかりません。\n")
            return "指定されたIDのメンバーが見つかりません。\n"
        if role is None:
            print("指定された名前のロールが見つかりません。\n")
            return "指定された名前のロールが見つかりません。\n"

        if role in member.roles:
            await member.remove_roles(role)
            print(f"{member.display_name} からロール {role.name} を削除しました。\n")
            return f"{member.display_name} からロール {role.name} を削除しました。\n"
        else:
            print(f"{member.display_name} はロール {role.name} を持っていません。\n")
            return f"{member.display_name} はロール {role.name} を持っていません。\n"
