import os
import re
import discord
from keep import keep_alive

from discord.ext import commands
from discord import ui, Interaction
from discord.ui import Button,Select,View
import csv
import random
import jaconv
import datetime
import time
import traceback
import json
from bson import ObjectId

from SpreadContent import SpreadContent
from MongoDB import MongoDB
from meowmeow import MeowMeow

meow = MeowMeow()
super_user = ["fine4139", "ayalovex0001", "liankuma"]


def contains_any_substring(main_string, substrings):
    return any(substring in main_string for substring in substrings)


class MessagePointContainer:
    def __init__(self, message):
        self.reg_elements = ["火", "水", "風", "光", "闇", "全"]
        self.reg_levels = ["180", "190", "200", "250", "275", "300", "325"]
        self.reg_points = ["10", "11", "12", "13", "14", "15",
                           "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        self.words_to_keep_reg = self.reg_elements+self.reg_levels+self.reg_points

        self.message = message
        parsed_list = self.extract_words_per_line(
            self.message, self.words_to_keep_reg)
        self.point_set_list = self.detect_pattern_in_list(parsed_list)

    def extract_words_per_line(self, text, words_to_keep):
        # 改行で分割
        lines = text.splitlines()
        all_results = []

        for line in lines:
            # 単語を正規表現のパターンに変換
            pattern = '|'.join(map(re.escape, words_to_keep))
            # 各行で単語を抽出し、リストに格納
            result = re.findall(pattern, line)
            # それぞれの単語を適切な型に変換
            result = [(word) if word.isdigit() else word for word in result]
            all_results.append(result)

        all_results = list(filter(None, all_results))
        print(all_results)
        return all_results

    def detect_pattern_in_list(self, parsed_list):

        print(parsed_list)
        new_parsed_list = []
        for line in parsed_list:
            new_parsed_list.append(
                self.convert_elements(line, '全', ["火", "水", "風", "光", "闇"]))

        print("new_parsed_list : ", new_parsed_list)

        element_count_list = []
        level_count_list = []
        point_count_list = []
        for line in new_parsed_list:
            element_count = 0
            level_count = 0
            point_count = 0
            for word in line:
                if word in self.reg_elements:
                    element_count += 1
                if word in self.reg_levels:
                    level_count += 1
                if word in self.reg_points:
                    point_count += 1
            element_count_list.append(element_count)
            level_count_list.append(level_count)
            point_count_list.append(point_count)

        output_list = []
        repeating_pattern_elements = []
        repeating_pattern_levels = []
        config_pattern_type = -1
        for i, line in enumerate(new_parsed_list):
            prediction_set_elements = []
            prediction_set_levels = []

            if level_count_list[i] + point_count_list[i] == 0:  # 例:対風対火対水
                config_pattern_type = 0
                repeating_pattern_elements = line

            elif element_count_list[i] + point_count_list[
                    i] == 0:  # 例:180 190 200
                config_pattern_type = 1
                repeating_pattern_levels = line

            elif config_pattern_type == 0:  # 例:180 1 2 3
                element_pos = 0
                for i, word in enumerate(line):
                    if word in self.reg_levels:
                        element_pos = i + 1
                        prediction_set_levels.append(word)
                    else:
                        for level in prediction_set_levels:
                            output_list.append({
                                "element":
                                repeating_pattern_elements[i - element_pos],
                                "level":
                                level,
                                "point":
                                word
                            })

            elif config_pattern_type == 1:  # 例:対風 対火 1 2 3
                level_pos = 0
                is_stop_element = False
                for i, word in enumerate(line):
                    if word in self.reg_elements and is_stop_element == False:
                        level_pos = i + 1
                        prediction_set_elements.append(word)
                    else:
                        is_stop_element = True
                        for element in prediction_set_elements:
                            output_list.append({
                                "element":
                                element,
                                "level":
                                repeating_pattern_levels[i - level_pos],
                                "point":
                                word
                            })

            elif config_pattern_type == -1:  # 例:対風 対火 180 1 190 2 対光 200 2
                level_point_set = {}
                level_point_is_processing = False
                for word in line:
                    if word in self.reg_elements:
                        if level_point_is_processing:
                            prediction_set_elements = []
                        level_point_is_processing = False
                        prediction_set_elements.append(word)
                    else:
                        level_point_is_processing = True
                        if word in self.reg_levels:
                            level_point_set["level"] = word
                        else:
                            level_point_set["point"] = word
                        if len(level_point_set) == 2:
                            for element in prediction_set_elements:
                                output_list.append({
                                    "element":
                                    element,
                                    "level":
                                    level_point_set["level"],
                                    "point":
                                    level_point_set["point"]
                                })
                            level_point_set = {}
        return output_list

    def convert_elements(self, original_list, target_element, new_list):
        result_list = []
        for item in original_list:
            if item == target_element:
                result_list.extend(new_list)
            else:
                result_list.append(item)
        return result_list

    def get_point_set_list(self):
        return self.point_set_list


class MessageTimelineContainer:
    def __init__(self, message, tl_author_other):
        self.message = message
        self.content = self.message.content
        self.author = self.message.author.display_name

        self.attack_types = ["スキル", "通攻"]
        self.my_elements = ["火", "水", "風", "光", "闇"]
        self.vs_elements = ["対火", "対水", "対風", "対光", "対闇"]
        self.tl_levels = ["180", "190", "200", "250", "275", "300", "325"]
        self.tl_points = ["1", "2", "3"]

        self.words_to_keep_tl = self.attack_types+self.my_elements + \
            self.vs_elements+self.tl_levels+self.tl_points

        self.tl_visibility = ["全表示", "全部"]
        self.tl_author_me = ["著", "私", "ぼく", "わたし",
                             "俺", "おれ", "オレ", "わい", "わたくし", "自分"]
        self.tl_author_other = tl_author_other
        print(self.tl_author_other)

        self.words_to_keep_search_tl = self.words_to_keep_tl + \
            self.tl_visibility+self.tl_author_me+self.tl_author_other

        self.json_string, self.is_tl = self.labeling_per_line(
            self.content)  # json.dumps(
        self.message_type = None
        self.search_type_dict = {"attack_type": None, "enemy_element": None,
                                 "enemy_level": None, "point": None, "author": None, "see_all": False}
        if (self.is_tl):
            self.tl_string = self.tl_all_printer(self.json_string)
            self.message_type = "TL"
            print(self.tl_string)
        else:
            self.message_type = self.analysis_message_type(self.content)

    def analysis_message_type(self, text):
        lines = text.splitlines()
        line = lines[0]
        please_list = ["表示", "欲しい", "要求", "please", "ほしい", "Please",
                       "プリーズ", "ぷりーず", "お願い", "くれにゃ", "くれニャ", "ください", "所望", "下さい"]
        pattern_please = '|'.join(map(re.escape, please_list))
        match_please = re.findall(pattern_please, line)

        delete_list = ["削除", "消し", "さくじょ", "消去",]
        pattern_delete = '|'.join(map(re.escape, delete_list))
        match_delete = re.findall(pattern_delete, line)

        correction_list = ["修正", "直し", "なおし", "なおす", "訂正"]
        pattern_correction = '|'.join(map(re.escape, correction_list))
        match_correction = re.findall(pattern_correction, line)

        if (len(match_delete) > 0):
            self.analysis_enemy_type(line)
            return "delete"
        elif (len(match_please) > 0):
            self.analysis_enemy_type(line)
            return "please"
        else:
            return "none"
        """
        elif(len(match_correction)>0):
            return "correction"
        """

    def analysis_enemy_type(self, line):

        # 単語を正規表現のパターンに変換
        pattern_tl = '|'.join(map(re.escape, self.words_to_keep_search_tl))
        # 各行で単語を抽出し、リストに格納
        result = re.findall(pattern_tl, line)
        # それぞれの単語を適切な型に変換
        result = [(word) if word.isdigit() else word for word in result]

        for word in result:
            if (word in self.attack_types):
                self.search_type_dict["attack_type"] = word
            elif (word in self.vs_elements):
                self.search_type_dict["enemy_element"] = word
            elif (word in self.my_elements):
                self.search_type_dict["enemy_element"] = self.vs_elements[self.my_elements.index(
                    word)]
            elif (word in self.tl_levels):
                self.search_type_dict["enemy_level"] = word
            elif (word in self.tl_points):
                self.search_type_dict["point"] = word
            elif (word in self.tl_visibility):
                self.search_type_dict["see_all"] = True
            elif (word in self.tl_author_other):
                self.search_type_dict["author"] = word
            elif (word in self.tl_author_me):
                self.search_type_dict["author"] = self.author
            else:
                pass

    def labeling_per_line(self, text):
        # 改行で分割
        time_len = 0
        lines = text.splitlines()
        labeling_results = []
        fight_times = {"1": 30, "2": 110, "3": 190}
        correction_time = datetime.timedelta(minutes=0, seconds=0)

        is_enemy_type_readed = False
        is_timer_reading = False
        is_first_timer_readed = False
        is_re_timer = False
        labeling_dict = {"attack_type": None, "enemy_element": None, "enemy_level": None, "point": "3",
                         "author": str(self.message.author.display_name), "party": None, "remarks": [], "timeline": [],
                         "post_date": str(datetime.date.today()), "discord_id": str(self.message.author),
                         "visibility": True, "time": int(time.time())}
        for i, line in enumerate(lines):
            labeling_result = []
            if (not is_enemy_type_readed):
                # 単語を正規表現のパターンに変換
                pattern_tl = '|'.join(map(re.escape, self.words_to_keep_tl))
                # 各行で単語を抽出し、リストに格納
                result = re.findall(pattern_tl, line)
                # それぞれの単語を適切な型に変換
                result = [(word) if word.isdigit()
                          else word for word in result]
                if (len(result)) >= 3:
                    for word in result:
                        if (word in self.attack_types):
                            labeling_dict["attack_type"] = word
                        elif (word in self.vs_elements):
                            labeling_dict["enemy_element"] = word
                        elif (word in self.my_elements):
                            labeling_dict["enemy_element"] = self.vs_elements[self.my_elements.index(
                                word)]
                        elif (word in self.tl_levels):
                            labeling_dict["enemy_level"] = word
                        elif (word in self.tl_points):
                            labeling_dict["point"] = word
                            if (word == "3"):
                                is_re_timer = True
                        else:
                            pass
                    is_enemy_type_readed = True
                else:
                    pass
            else:
                # 同じ文字が8回以上連続するパターン
                pattern_partition = r'(.)\1{7,}'
                # パターンにマッチするすべての部分を検索
                matches_partition = re.findall(pattern_partition, line)

                # 分:秒の形式を表す正規表現パターン
                pattern_time = r'\b\d{1}[:：]\d{2}\b'
                pattern_time_sub = r'\b\d{1,2}[:：]\d{2}\b\s*'
                # パターンにマッチするすべての部分を検索
                matches_time = re.findall(pattern_time, line)

                pattern_party = "編成"
                matches_party = re.findall(pattern_party, line)

                if (len(matches_time) > 0):
                    is_timer_reading = True
                    timer_string = matches_time[0]
                    line = re.sub(pattern_time_sub, '', line)
                    # 分と秒を分離
                    minutes, seconds = map(int, re.split(
                        r'[:：]', timer_string))  # コロンで分割
                    left_minutes = minutes * 60 + seconds

                    if (not is_first_timer_readed):
                        if (abs(fight_times[labeling_dict["point"]]-left_minutes) <= abs(fight_times["3"]-left_minutes)):
                            is_re_timer = True
                        else:
                            is_re_timer = False
                        is_first_timer_readed = True
                        correction_time = fight_times["3"] - \
                            fight_times[labeling_dict["point"]]

                    time_obj_minutes, time_obj_seconds = divmod(
                        left_minutes, 60)
                    if (labeling_dict["point"] != "3"):
                        if (not is_re_timer):
                            im_time_obj_minutes, im_time_obj_seconds = divmod(
                                (left_minutes-correction_time), 60)
                            line = str(time_obj_minutes)+":"+str(time_obj_seconds).zfill(2)+"\t"+str(
                                im_time_obj_minutes)+":"+str(im_time_obj_seconds).zfill(2)+line
                        else:
                            re_time_obj_minutes, re_time_obj_seconds = divmod(
                                (left_minutes+correction_time), 60)
                            line = str(re_time_obj_minutes)+":"+str(re_time_obj_seconds).zfill(
                                2)+"\t"+str(time_obj_minutes)+":"+str(time_obj_seconds).zfill(2)+line
                    else:
                        line = str(time_obj_minutes)+":" + \
                            str(time_obj_seconds).zfill(2)+"\t"+line
                    labeling_result = ["timeline", line]

                elif (len(matches_partition) > 0):
                    labeling_result = ["partition1", line]
                elif (len(line) == 0):
                    labeling_result = ["partition2", line]
                elif (len(matches_party) > 0):
                    labeling_result = ["party", line]
                elif (is_enemy_type_readed):
                    if (is_timer_reading):
                        labeling_result = ["supplement", line]
                    else:
                        labeling_result = ["remarks", line]

            if (len(labeling_result) != 0):
                labeling_results.append(labeling_result)

        for result in labeling_results:
            if (result[0] == "remarks"):
                labeling_dict["remarks"].append(result[1])
            elif (result[0] == "timeline"):
                time_len += 1
                labeling_dict["timeline"].append(result[1])
            elif (result[0] == "partition1"):
                labeling_dict["timeline"].append(result[1])
            elif (result[0] == "partition2"):
                labeling_dict["timeline"].append(result[1])
            elif (result[0] == "party"):
                labeling_dict["party"] = result[1]
            elif (result[0] == "supplement"):
                labeling_dict["timeline"].append(result[1])
        if (time_len < 3):
            return None, False
        else:
            return labeling_dict, True

    def tl_all_printer(self, doc):
        output_string = ""
        output_string += "【"
        if (doc["attack_type"] != None):
            output_string += doc["attack_type"]
        output_string += doc["enemy_element"]+doc["enemy_level"]
        output_string += "の"
        output_string += doc["point"]+"P "
        output_string += doc["author"]
        output_string += "著 "
        output_string += "作成日"
        output_string += doc["post_date"]+"】\n"
        output_string += doc["party"]+"\n"
        for text in doc["remarks"]:
            output_string += text+"\n"
        output_string += "\n"
        for timeline in doc["timeline"]:
            output_string += timeline+"\n"
        return output_string


class MyBot(commands.Bot):

    def __init__(self, command_prefix='!', *args, **kwargs):
        super().__init__(command_prefix, *args, **kwargs)


    async def on_ready(self):
        print(f'ログインしました: {self.user}')
        
    
    async def setup_hook(self):
        # Botが起動する際に、Cogをロード
        await self.add_cog(messageManager(self))

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
                self.author_name = str(self.message.author.display_name)
                self.author_id = str(self.message.author)
                await self.on_point_message()
            elif self.message.channel.name == "タイムライン管理所":
                self.author_name = str(self.message.author.display_name)
                self.author_id = str(self.message.author)
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
            
            command_names=["代理","名前登録","csv","生存確認","名前確認","名前変更","名前削除"]
            # 正規表現でダブルクォーテーションで囲まれた部分をすべて抽出
            command_arg_matches = re.findall(r'["\'\[\](){}<>]([^\0"\[\]\'\(\)\{\}<>]+)["\'\[\](){}<>]', str(self.message.content))
            # コマンド名がメッセージ内に含まれているかチェック
            found_commands = [command for command in command_names if command in str(self.message.content)]

            self.is_meow = meow.meowmeow_check(str(self.message.content))
            is_agent = False
            is_sudo = str(self.message.author) in super_user
            self.return_message = f"{self.message.author.mention} "
            self.return_view = View()

            self.registrant_name = str(self.message.author.display_name)
            self.registrant_id = str(self.message.author)

            print("送信者の名前 : ", self.registrant_name, self.author_id)

            if "代理" in found_commands:
                if (is_sudo):
                    if(len(command_arg_matches)!=0):
                        registrant_name_or_id = command_arg_matches.pop(0)

                        if(self.spread_content.id_exists(registrant_name_or_id)):
                            self.registrant_name = self.spread_content.convert_id_to_name(registrant_name_or_id)
                            self.registrant_id = registrant_name_or_id
                        elif(self.spread_content.name_exists(registrant_name_or_id)):
                            self.registrant_name = registrant_name_or_id
                            self.registrant_id = ""
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
            self.return_view.add_item(DynamicOkButton(self.bot, self.message.author.id, self.is_meow, self.register_name, registrant_name=registrant_name))
            self.return_message += meow.meowmeow_accent(f"{registrant_name}さんを登録しますか？", self.is_meow)
    
    def register_name(self, registrant_name):
        try:
            send_message = self.spread_content.registered_name(registrant_name, self.registrant_id)
            return send_message,None
        except Exception as e:
            error_message = traceback.format_exc()
            return f"予期しないエラーが発生しました: {e}\n" + error_message,None
            print(f"予期しないエラーが発生しました: {e}\n"+error_message)


    def delete_name_check(self, delete_name):
        cell_pos = self.spread_content.find_name_pos(delete_name) - 3
        if (cell_pos < 0):
            self.return_message += meow.meowmeow_accent("ERROR: 名前が見つかりませんでした。",self.is_meow)
        else:
            self.return_view.add_item(DynamicOkButton(self.bot, self.message.author.id, self.is_meow, self.delete_name, delete_name=delete_name))
            self.return_message += meow.meowmeow_accent(f"{delete_name}さんを削除しますか？",self.is_meow)

    def delete_name(self, delete_name):
        try:
            send_message = self.spread_content.delete_name(delete_name, is_meow=self.is_meow)
            return send_message,None
        except Exception as e:
            error_message = traceback.format_exc()
            return f"予期しないエラーが発生しました: {e}\n" + error_message,None
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

                self.return_view.add_item(DynamicOkButton(self.bot, self.message.author.id, self.is_meow, self.register_point, unupdated_list=unupdated_list))


    def register_point(self, unupdated_list):
        try:
            send_message = ""
            self.spread_content.register_point(unupdated_list)
            send_message += meow.meowmeow_accent("更新しました！\n",self.is_meow)

            for unupdated_point in unupdated_list:
                return_row_message = unupdated_point["element"] + unupdated_point["level"] + "\t" +  unupdated_point["registered_point"] + "→" + unupdated_point["point"] + "\n"
                send_message += return_row_message
            return send_message,None
        except Exception as e:
            error_message = traceback.format_exc()
            return f"予期しないエラーが発生しました: {e}\n" + error_message,None
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
            await self.message.channel.send(f"予期しないエラーが発生しました: {e}\n"+error_message),None
            print(f"予期しないエラーが発生しました: {e}\n"+error_message)

    def register_timeline_check(self):
        self.return_message += meow.meowmeow_accent("以下のタイムラインを登録しますか？\n",self.is_meow)
        self.return_message += self.messageTimelineContainer.tl_string
        self.return_view.add_item(DynamicOkButton(self.bot, self.message.author.id, self.is_meow, self.register_timeline))

    def register_timeline(self):
        try:
            send_message = self.mongo_db.insert_tl(self.messageTimelineContainer.json_string)
            return send_message,None
        except Exception as e:
            error_message = traceback.format_exc()
            return f"予期しないエラーが発生しました: {e}\n" + error_message,None
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

            self.return_view.add_item(DynamicSelectMenu(self.bot, self.message.author.id, self.is_meow, self.please_timeline, options))


    def please_timeline(self,selected_value):
        send_message = meow.meowmeow_accent("選択したタイムラインです\n", self.is_meow)
        document = self.mongo_db.search_tl_id(ObjectId(selected_value))
        send_message += self.messageTimelineContainer.tl_all_printer(document)
        return send_message,None


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
            self.return_message += meow.meowmeow_accent("の条件で検索しました\n",self.is_meow)

        self.return_message += meow.meowmeow_accent("削除したいタイムラインを選択してください\n",self.is_meow)

        self.return_view.add_item(DynamicSelectMenu(self.bot, self.message.author.id, self.is_meow, self.delete_timeline, options))

    def really_delete_check(self,selected_value):
        send_message = meow.meowmeow_accent("本当にこのタイムラインを削除しますか？\n", self.is_meow)
        self.return_view.add_item(DynamicSelectMenu(self.bot, self.message.author.id, self.is_meow, self.delete_timeline, ObjectId(selected_value)))
        return send_message,self.return_view

    def delete_timeline(self,selected_value):
        send_message = meow.meowmeow_accent("削除しました\n", self.is_meow)
        self.mongo_db.delete_tl(ObjectId(selected_value))
        return send_message,None
    


"""
class RenameOKButton(ui.Button):

    def __init__(self,
                    *,
                    label='OK',
                    spread_sheet: SpreadContent,
                    old_name: str,
                    new_name: str,
                    is_meow: bool,
                    **kwargs):
        self.spread_sheet = spread_sheet
        self.old_name = old_name
        self.new_name = new_name
        self.is_meow = is_meow
        super().__init__(label=label, **kwargs)

    async def callback(self, interaction: Interaction):
        try:
            await interaction.response.defer(thinking=True)
            send_message = self.spread_sheet.rename_name(
                old_name=self.old_name,
                new_name=self.new_name,
                is_meow=self.is_meow)

            await interaction.followup.send(content=send_message)
            self.view.stop()
        except Exception as e:
            error_message = traceback.format_exc()
            await interaction.followup.send(content=f"予期しないエラーが発生しました: {e}\n"+error_message)
            print(f"予期しないエラーが発生しました: {e}\n"+error_message)
"""

class DynamicOkButton(Button):
    def __init__(self, bot, author_id, is_meow, action,**kwargs):
        self.bot = bot
        self.user_id = author_id
        self.is_meow = is_meow
        self.action = action  # 実行する関数
        self.kwargs = kwargs  # 必要な追加情報
        super().__init__(label="OK", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        try:
            if interaction.user.id != self.user_id:
                pass
            else:
                # 動的に設定された処理を実行
                await interaction.response.defer(thinking=True)
                return_view=View()
                return_message,return_view_ui = self.action(**self.kwargs)
                if(return_view_ui!=None):
                    return_view.add_item(return_view_ui)
                await interaction.followup.send(content=return_message,view=return_view)
        except Exception as e:
            error_message = traceback.format_exc()
            await interaction.followup.send(content=f"予期しないエラーが発生しました: {e}\n"+error_message)
            print(f"予期しないエラーが発生しました: {e}\n"+error_message)

class DynamicSelectMenu(Select):
    def __init__(self, bot, author_id, is_meow, action, options , **kwargs):
        super().__init__(options = options)
        self.bot = bot
        self.user_id = author_id
        self.is_meow = is_meow
        self.action = action  # 実行する関数
        self.options = options
        self.kwargs = kwargs

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            pass
        else:
            try:
                await interaction.response.defer(thinking=True)
                return_view=View()
                return_message,return_view_ui = self.action(self.values[0] , **self.kwargs)
                if(return_view_ui!=None):
                    return_view.add_item(return_view_ui)
                await interaction.followup.send(content=return_message,view=return_view)
            except Exception as e:
                error_message = traceback.format_exc()
                await interaction.followup.send(content=f"予期しないエラーが発生しました: {e}\n"+error_message)
                print(f"予期しないエラーが発生しました: {e}\n"+error_message)



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