import os
import re
import discord
from keep import keep_alive

from discord.ext import commands
from discord.ui import Button,Select,View
import csv
import jaconv
import traceback
from bson import ObjectId

from SpreadContent import SpreadContent
from MongoDB import MongoDB
from meowmeow import MeowMeow
from MessagePointContainer import MessagePointContainer
from MessageTimelineContainer import MessageTimelineContainer
from DynamicUi import DynamicOkButton,DynamicSelectMenu

meow = MeowMeow()
super_user = ["fine4139", "ayalovex0001", "liankuma"]


def contains_any_substring(main_string, substrings):
    return any(substring in main_string for substring in substrings)




class MyBot(commands.Bot):

    def __init__(self, command_prefix='!', *args, **kwargs):
        super().__init__(command_prefix, *args, **kwargs)


    async def on_ready(self):
        print(f'ログインしました: {self.user}')
        
    
    async def setup_hook(self):
        # Botが起動する際に、Cogをロード
        await self.add_cog(messageManager(self))

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


class messageManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spread_content = SpreadContent()
        self.mongo_db = MongoDB()

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            self.message = message
            if self.message.author.bot:
                return
            elif self.message.channel.name == "戦力報告専用":
                #self.spread_content.read_strong_attributes_cells("300")
                self.author_name = str(self.message.author.display_name)
                self.author_user_id = str(self.message.author)
                await self.on_point_message()
            elif self.message.channel.name == "タイムライン管理所":
                self.author_name = str(self.message.author.display_name)
                self.author_user_id = str(self.message.author)
                await self.on_timeline_message()
            else:
                return
        except Exception as e:
            error_message = traceback.format_exc()
            await message.channel.send(f"予期しないエラーが発生しました: {e}\n"+error_message)
            print(f"予期しないエラーが発生しました: {e}\n"+error_message)


    async def on_point_message(self):
        try:
            await self.message.add_reaction("🤔")
            
            command_names=["代理","名前登録","csv","生存確認","名前確認","名前変更","名前削除","ロール表示","ロール付与"]
            # 正規表現でダブルクォーテーションで囲まれた部分をすべて抽出
            command_arg_matches = re.findall(r'["\'\[\](){}<>]([^\0"\[\]\'\(\)\{\}<>]+)["\'\[\](){}<>]', str(self.message.content))
            # コマンド名がメッセージ内に含まれているかチェック
            found_commands = [command for command in command_names if command in str(self.message.content)]

            self.is_meow = meow.meowmeow_check(str(self.message.content))
            is_agent = False
            is_sudo = str(self.author_user_id) in super_user
            self.return_message = f"{self.message.author.mention} "
            self.return_view = View()

            self.registrant_name = str(self.message.author.display_name)
            self.registrant_user_id = str(self.author_user_id)
            self.message_guild_id = self.message.guild.id

            print("送信者の名前 : ", self.registrant_name, self.author_user_id)

            if "代理" in found_commands:
                if (is_sudo):
                    if(len(command_arg_matches)!=0):
                        registrant_name_or_id = command_arg_matches.pop(0)

                        if(self.spread_content.id_exists(registrant_name_or_id)):
                            self.registrant_name = self.spread_content.convert_id_to_name(registrant_name_or_id)
                            self.registrant_user_id = registrant_name_or_id
                        elif(self.spread_content.name_exists(registrant_name_or_id)):
                            self.registrant_name = registrant_name_or_id
                            self.registrant_user_id = ""
                        else:
                            self.return_message += meow.meowmeow_accent("ERROR: その人物は存在しないです！", self.is_meow)
                            await self.message.channel.send(self.return_message,view=self.return_view)
                            return
                        is_agent = True
                        found_commands.pop(0)
                    else:
                        self.return_message += meow.meowmeow_accent("ERROR: 代理したい人の名前が記述されていません！", self.is_meow)
                else:
                    self.return_message+=meow.meowmeow_accent("ERROR: 権限がありません！", self.is_meow)
                    await self.message.channel.send(self.return_message,view=self.return_view)
                    return


            if(len(found_commands)!=0):
                if '名前登録' in found_commands:
                    if(is_sudo):
                        if(len(command_arg_matches)!=0):
                            self.register_name_check(command_arg_matches[0])
                        else:
                            self.return_message += meow.meowmeow_accent("ERROR: 登録しようとしている名前が記述されていません！", self.is_meow)
                    else:
                        self.return_message += meow.meowmeow_accent("ERROR: 権限がありません！", self.is_meow)
                    await self.message.channel.send(self.return_message,view=self.return_view)
                    return

                elif 'csv' in found_commands:
                    self.return_message += self.print_csv()
                    await self.message.channel.send(self.return_message, file=discord.File("output.csv", 'output.csv'))
                    return

                elif "生存確認" in found_commands:
                    self.return_message += meow.meowmeow_accent("こんにちは！", self.is_meow)
                    await self.message.channel.send(self.return_message,view=self.return_view)
                    await self.message.remove_reaction("🤔", self.message.guild.me)
                    await self.message.add_reaction("🥰")
                    return


                elif '名前削除' in found_commands:
                    if (is_sudo):
                        if(len(command_arg_matches)!=0):
                            self.delete_name_check(command_arg_matches[0])
                        else:
                            self.return_message += meow.meowmeow_accent("ERROR: 登録しようとしている名前が記述されていません！", self.is_meow)
                    else:
                        self.return_message += meow.meowmeow_accent("ERROR: 権限がありません！", self.is_meow)
                    await self.message.channel.send(self.return_message,view=self.return_view)
                    return

                elif "ロール表示" in found_commands:
                    dust_list = self.bot.list_members(self.message_guild_id)
                    #self.return_message += meow.meowmeow_accent("", self.is_meow)
                    await self.message.remove_reaction("🤔", self.message.guild.me)
                    await self.message.channel.send(self.return_message,view=self.return_view)
                    
                elif "ロール付与" in found_commands:
                    role_level = "300"
                    if(len(command_arg_matches)!=0):
                        role_level = command_arg_matches.pop(0)
                    
                    assignment_roles_list = self.spread_content.read_strong_attributes_cells(str(role_level))
                    member_roles_list = self.bot.list_members(self.message_guild_id)

                    for user_name in member_roles_list:
                        if user_name in assignment_roles_list:
                            print(user_name)
                            include_elements = ["同盟在籍者","対火","対水","対風","対光","対闇"]  # 除外しない要素

                            # member_roles_list[user_name]にあってassignment_roles_list[user_name]にはない要素をdelete_roles_listに格納（ただしinclude_elementsに含まれるもののみ）
                            delete_roles_list = []
                            for item in member_roles_list[user_name]:
                                if item not in assignment_roles_list[user_name] and item in include_elements:
                                    delete_roles_list.append(item)

                            # assignment_roles_list[user_name]にあってmember_roles_list[user_name]にはない要素をadd_roles_listに格納（ただしinclude_elementsに含まれるもののみ）
                            add_roles_list = []
                            for item in assignment_roles_list[user_name]:
                                if item not in member_roles_list[user_name] and item in include_elements:
                                    add_roles_list.append(item)
                            if(len(add_roles_list) != 0 or len(delete_roles_list) != 0):
                                self.return_message += "\n"
                            for role in add_roles_list:
                                self.return_message += meow.meowmeow_accent(await self.bot.add_role(self.message_guild_id,user_name,role), self.is_meow)
                            for role in delete_roles_list:
                                self.return_message += meow.meowmeow_accent(await self.bot.delete_role(self.message_guild_id,user_name,role), self.is_meow)
                        else:
                            include_elements = ["同盟在籍者","対火","対水","対風","対光","対闇"]  # 除外しない要素
                            for role in member_roles_list[user_name]:
                                if role in include_elements:
                                    self.return_message += meow.meowmeow_accent(await self.bot.delete_role(self.message_guild_id,user_name,role), self.is_meow)

                    #print(member_roles_list, assignment_roles_list)
                    self.return_message += meow.meowmeow_accent("すべてのロールを付与しました！", self.is_meow)
                    await self.message.remove_reaction("🤔", self.message.guild.me)
                    await self.message.channel.send(self.return_message,view=self.return_view)
                """
                elif '名前変更' in found_commands:
                    if (not self.spread_content.name_exists(registrant_name)):
                        return_message+=meow.meowmeow_accent("ERROR: 指定の名前の人物は見つかりませんでした。",self.is_meow)
                    elif (self.spread_content.name_exists(splited_message[1])):
                        return_message+=meow.meowmeow_accent("ERROR: 名前が被っています！",self.is_meow)

                    else:
                        return_view = ui.View()  # Viewインスタンスを作成
                        button_RN = self.RenameOKButton(
                            label='OK',
                            style=discord.ButtonStyle.green,
                            custom_id=str(message.author) + "_registrant_name",
                            spread_sheet=self.spread_content,
                            old_name=str(registrant_name),
                            new_name=splited_message[1],
                            self.is_meow=self.is_meow)  # Buttonインスタンスを作成

                        return_message += meow.meowmeow_accent(f"{registrant_name}さんの名前を{splited_message[1]}に変更しますか？",self.is_meow)
                        return_view.add_item(button_RN)
                """
            else:
                self.analysis_point_spreadsheet()  # ポイント解析
                if(self.return_message != f"{self.message.author.mention} "):
                    await self.message.channel.send(self.return_message,view=self.return_view)
                else:
                    if self.is_meow:
                        self.return_message += meow.meowmeow_return()
                        await self.message.remove_reaction("🤔", self.message.guild.me)
                        await self.message.add_reaction("🐈")
                        await self.message.channel.send(self.return_message, view=self.return_view)
                        return
                    else:
                        await self.message.remove_reaction("🤔", self.message.guild.me)
                        return
        except Exception as e:
            error_message = traceback.format_exc()
            await self.message.channel.send(f"予期しないエラーが発生しました: {e}\n"+error_message)
            print(f"予期しないエラーが発生しました: {e}\n"+error_message)


    def register_name_check(self, registrant_name):
        is_registered_name = self.spread_content.name_exists(registrant_name)
        if (is_registered_name):
            self.return_message += meow.meowmeow_accent("ERROR: 既に登録されています！", self.is_meow)
        else:
            self.return_view.add_item(DynamicOkButton(self.bot, self.author_user_id, self.is_meow, self.register_name, registrant_name=registrant_name))
            self.return_message += meow.meowmeow_accent(f"{registrant_name}さんを登録しますか？", self.is_meow)
    
    def register_name(self, registrant_name):
        try:
            send_message = self.spread_content.registered_name(registrant_name, self.registrant_user_id)
            return send_message,View()
        except Exception as e:
            error_message = traceback.format_exc()
            return f"予期しないエラーが発生しました: {e}\n" + error_message,View()
            print(f"予期しないエラーが発生しました: {e}\n"+error_message)


    def delete_name_check(self, delete_name):
        cell_pos = self.spread_content.find_name_pos(delete_name) - 3
        if (cell_pos < 0):
            self.return_message += meow.meowmeow_accent("ERROR: 名前が見つかりませんでした。",self.is_meow)
        else:
            self.return_view.add_item(DynamicOkButton(self.bot, self.author_user_id, self.is_meow, self.delete_name, delete_name=delete_name))
            self.return_message += meow.meowmeow_accent(f"{delete_name}さんを削除しますか？",self.is_meow)

    def delete_name(self, delete_name):
        try:
            send_message = self.spread_content.delete_name(delete_name)
            return send_message,View()
        except Exception as e:
            error_message = traceback.format_exc()
            return f"予期しないエラーが発生しました: {e}\n" + error_message,View()
            print(f"予期しないエラーが発生しました: {e}\n"+error_message)

    def print_csv(self):
        self.spread_content.get_name_len()
        all_spread_data = self.spread_content.get_cells(
            self.spread_content.x_pos, self.spread_content.y_pos, self.spread_content.x_len, self.spread_content.name_len)
        header = self.spread_content.get_cells(self.spread_content.x_pos + 1, 1, self.spread_content.x_len, 1)

        for row in all_spread_data:
            if (len(row) >= 2):
                del row[1]
        header[0][0] = "名前"
        all_spread_data.insert(0, header[0])
        with open('output.csv', 'w') as f:
            writer = csv.writer(f, delimiter=',')
            for row_data in all_spread_data:
                writer.writerow(row_data)
            f.close()

        self.return_message += meow.meowmeow_accent("送信しました！", self.is_meow)
        return self.return_message


    def analysis_point_spreadsheet(self):
        print(self.message.content)
        messagePointContainer = MessagePointContainer(self.message.content)
        point_set_list = messagePointContainer.get_point_set_list()
        if (len(point_set_list) > 0):
            is_registered_name, unupdated_list = self.spread_content.find_point(self.registrant_name, point_set_list)

            if (len(unupdated_list) == 0 and len(point_set_list) > 0):
                self.return_message += meow.meowmeow_accent(f"最新の状態です！",self.is_meow)

            elif (is_registered_name):
                self.return_message += meow.meowmeow_accent(f"以下の内容でよいなら更新をポチっと押してください\n",self.is_meow)
                self.return_message += self.registrant_name + "さん\n"
                for unupdated_point in unupdated_list:
                    return_row_message = ""
                    return_row_message = unupdated_point[
                        "element"] + unupdated_point[
                            "level"] + "\t" + unupdated_point[
                                "registered_point"] + "→" + unupdated_point[
                                    "point"] + "\n"
                    self.return_message += return_row_message

                self.return_view.add_item(DynamicOkButton(self.bot, self.author_user_id, self.is_meow, self.register_point, unupdated_list=unupdated_list))


    def register_point(self, unupdated_list):
        try:
            send_message = ""
            self.spread_content.register_point(unupdated_list)
            send_message += meow.meowmeow_accent("更新しました！\n",self.is_meow)

            for unupdated_point in unupdated_list:
                return_row_message = unupdated_point["element"] + unupdated_point["level"] + "\t" +  unupdated_point["registered_point"] + "→" + unupdated_point["point"] + "\n"
                send_message += return_row_message
            return send_message,View()
        except Exception as e:
            error_message = traceback.format_exc()
            return f"予期しないエラーが発生しました: {e}\n" + error_message,View()
            print(f"予期しないエラーが発生しました: {e}\n" + error_message)





    async def on_timeline_message(self):
        try:
            await self.message.add_reaction("🤔")
            self.is_meow = meow.meowmeow_check(str(self.message.content))
            tl_author_other = self.mongo_db.distinct_tl("author")

            self.return_message = f"{self.message.author.mention} "
            self.return_view = View()
            self.messageTimelineContainer = MessageTimelineContainer(self.message, tl_author_other)
            if (self.messageTimelineContainer.message_type == "TL"):
                self.register_timeline_check()
                
            elif (self.messageTimelineContainer.message_type == "please"):
                self.please_timeline_check()

            elif (self.messageTimelineContainer.message_type == "delete"):
                self.delete_timeline_check()

            elif (self.messageTimelineContainer.message_type == "none"):
                if (self.is_meow):
                    self.return_message += meow.meowmeow_return()

            if (self.return_message != f"{self.message.author.mention} "):
                await self.message.channel.send(self.return_message, view=self.return_view)
            else:
                await self.message.remove_reaction("🤔", self.message.guild.me)
        except Exception as e:
            error_message = traceback.format_exc()
            await self.message.channel.send(f"予期しないエラーが発生しました: {e}\n"+error_message),View()
            print(f"予期しないエラーが発生しました: {e}\n"+error_message)

    def register_timeline_check(self):
        self.return_message += meow.meowmeow_accent("以下のタイムラインを登録しますか？\n",self.is_meow)
        self.return_message += self.messageTimelineContainer.tl_string
        self.return_view.add_item(DynamicOkButton(self.bot, self.author_user_id, self.is_meow, self.register_timeline))

    def register_timeline(self):
        try:
            send_message = self.mongo_db.insert_tl(self.messageTimelineContainer.json_string)
            return send_message,View()
        except Exception as e:
            error_message = traceback.format_exc()
            return f"予期しないエラーが発生しました: {e}\n" + error_message,View()
            print(f"予期しないエラーが発生しました: {e}\n"+error_message)

    def please_timeline_check(self):
        element = self.messageTimelineContainer.search_type_dict["enemy_element"]
        level = self.messageTimelineContainer.search_type_dict["enemy_level"]
        point = self.messageTimelineContainer.search_type_dict["point"]
        attack_type = self.messageTimelineContainer.search_type_dict["attack_type"]
        author = self.messageTimelineContainer.search_type_dict["author"]
        see_all = self.messageTimelineContainer.search_type_dict["see_all"]

        search_query_list = [element, level,
                                point, attack_type, author]

        tls = self.mongo_db.search_tl(
            element=element, level=level, attack_type=attack_type, point=point, author=author, see_all=see_all)
        options = []
        if(len(tls)==0):
            self.return_message += meow.meowmeow_accent("その条件のタイムラインは見つかりませんでした。",self.is_meow)
        else:
            for tl in tls:
                label_text = ""
                if (tl["attack_type"] != None):
                    label_text += tl["attack_type"]
                label_text += tl["enemy_element"]+tl["enemy_level"]
                label_text += "の"
                label_text += tl["point"]+"P "
                label_text += tl["author"]
                label_text += "著 "
                label_text += "作成日"
                label_text += tl["post_date"]

                description_text = ""
                party_text = tl["party"]
                # カタカナを半角に変換
                party_text = jaconv.z2h(
                    party_text, kana=True, ascii=True, digit=True)
                description_text += party_text

                option = discord.SelectOption(
                    label=label_text, description=description_text, value=str(tl["_id"]))
                options.append(option)

            query_text = ""
            for query in search_query_list:
                if (query != None):
                    query_text += query+" "

            if (query_text != ""):
                self.return_message += query_text
                self.return_message += meow.meowmeow_accent("の条件で検索しました\n",self.is_meow)

            self.return_message += meow.meowmeow_accent("表示したいタイムラインを選択してください\n",self.is_meow)

            self.return_view.add_item(DynamicSelectMenu(self.bot, self.author_user_id, self.is_meow, self.please_timeline, options))


    def please_timeline(self,selected_value):
        send_message = meow.meowmeow_accent("選択したタイムラインです\n", self.is_meow)
        document = self.mongo_db.search_tl_id(ObjectId(selected_value))
        send_message += self.messageTimelineContainer.tl_all_printer(document)
        return send_message,View()


    def delete_timeline_check(self):
        element = self.messageTimelineContainer.search_type_dict["enemy_element"]
        level = self.messageTimelineContainer.search_type_dict["enemy_level"]
        point = self.messageTimelineContainer.search_type_dict["point"]
        attack_type = self.messageTimelineContainer.search_type_dict["attack_type"]
        author = self.messageTimelineContainer.search_type_dict["author"]
        see_all = self.messageTimelineContainer.search_type_dict["see_all"]

        search_query_list = [element, level,
                                point, attack_type, author]

        tls = self.mongo_db.search_tl(
            element=element, level=level, attack_type=attack_type, point=point, author=author, see_all=see_all)
        options = []
        if(len(tls)==0):
            self.return_message += meow.meowmeow_accent("その条件のタイムラインは見つかりませんでした。",self.is_meow)
        else:
            for tl in tls:
                label_text = ""
                if (tl["attack_type"] != None):
                    label_text += tl["attack_type"]
                label_text += tl["enemy_element"]+tl["enemy_level"]
                label_text += "の"
                label_text += tl["point"]+"P "
                label_text += tl["author"]
                label_text += "著 "
                label_text += "作成日"
                label_text += tl["post_date"]

                description_text = ""
                party_text = tl["party"]
                # カタカナを半角に変換
                party_text = jaconv.z2h(
                    party_text, kana=True, ascii=True, digit=True)
                description_text += party_text

                option = discord.SelectOption(
                    label=label_text, description=description_text, value=str(tl["_id"]))
                options.append(option)

            query_text = ""
            for query in search_query_list:
                if (query != None):
                    query_text += query+" "

            if (query_text != ""):
                self.return_message += query_text
                self.return_message += meow.meowmeow_accent("の条件で検索しました\n",self.is_meow)

        self.return_message += meow.meowmeow_accent("削除したいタイムラインを選択してください\n",self.is_meow)
        print(self.author_user_id)
        self.return_view.add_item(DynamicSelectMenu(self.bot, self.author_user_id, self.is_meow, self.really_delete_check, options, id = self.author_user_id))

    def really_delete_check(self, selected_value, id):
        send_message = meow.meowmeow_accent("本当にこのタイムラインを削除しますか？\n", self.is_meow)
        self.return_view = View()
        print(self.author_user_id, id)
        self.return_view.add_item(DynamicOkButton(self.bot, id, self.is_meow, self.delete_timeline, id = ObjectId(selected_value)))
        return send_message, self.return_view

    def delete_timeline(self,id):
        send_message = meow.meowmeow_accent("削除しました！\n", self.is_meow)
        self.mongo_db.delete_tl(id)
        return send_message,View()
    




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