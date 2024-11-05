import os
import re
import discord
from keep import keep_alive

from discord.ext import commands
from discord import ui, Interaction
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


super_user = ["fine4139", "ayalovex0001", "liankuma"]

meowmeow_input = []
meowmeow_raw = [
    "ごろごろ", "にゃっ", "にゃー", "にゃーん", "にゃーお", "にゃん", "にゃおーん", "にゃんにゃん", "にゃお",
    "にゃにゃ", "にゃにゃっ", "にゃにゃにゃ", "にゃおー", "にゃにゃーん", "にゃーご", "にゃ", "なーん"
]

meowmeow_input += meowmeow_raw
meowmeow_input += [meow.replace("に", "み") for meow in meowmeow_input]
meowmeow_input += [jaconv.hira2kata(meow) for meow in meowmeow_input]
meowmeow_input += [meow.replace("ー", "～") for meow in meowmeow_input]
meowmeow_output = meowmeow_input.copy()
meowmeow_output += [str(meow) + "！" for meow in meowmeow_input]

meowmeow_input += ["🐱", "🐈", "🐾", "😺", "😸",
                   "😹", "😻", "😼", "😽", "🙀", "😿", "😾", "シャー"]


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
        self.spread_content = SpreadContent()
        self.mongo_db = MongoDB()

    async def on_ready(self):
        print(f'ログインしました: {self.user}')

    async def on_message(self, message):
        try:
            if message.author.bot:
                return
            elif message.channel.name == "戦力報告専用":
                await self.on_register_message(message)
            elif message.channel.name == "タイムライン管理所":
                await self.on_timeline_message(message)
            else:
                return
        except Exception as e:
            error_message = traceback.format_exc()
            await message.channel.send(f"予期しないエラーが発生しました: {e}\n"+error_message)
            print(f"予期しないエラーが発生しました: {e}\n"+error_message)

    async def on_register_message(self, message):
        try:
            await message.add_reaction("🤔")
            is_meow = contains_any_substring(
                str(message.content), meowmeow_input)
            return_message = f"{message.author.mention} "
            return_view = None
            splited_message = re.split('[ |\n]', message.content)

            register_name = str(message.author.display_name)
            registrant_id = str(message.author)
            if (self.spread_content.id_exists(str(message.author))):
                register_name = self.spread_content.convert_name_to_id(
                    str(message.author))
                print(register_name)
            print("送信者の名前 : ", register_name, message.author)

            is_agent = False
            if splited_message[0] == "代理" and len(splited_message) >= 3:
                if (str(message.author) in super_user):
                    register_name = splited_message[1]
                    registrant_id = ""
                    is_agent = True
                    splited_message.pop(0)
                    splited_message.pop(0)
                else:
                    if (is_meow):
                        return_message += "えらー: 権限がありませんにゃ！"
                    else:
                        return_message += "ERROR: 権限がありません！"
                    await message.channel.send(return_message)
                    return
            elif splited_message[0] == "代理" and len(splited_message) < 3:
                if (is_meow):
                    return_message += "えらー: 不正なメッセージ形式ですにゃ！"
                else:
                    return_message += "ERROR: 不正なメッセージ形式です！"

                await message.channel.send(return_message, view=return_view)
                return

            is_registered_name = self.spread_content.name_exists(register_name)

            if splited_message[0] == '名前登録':  # 送信者の名前とIDが登録されておらず、登録する場合
                if (is_registered_name):
                    if (is_meow):
                        return_message += "えらー: 既に登録されていますにゃ！"
                    else:
                        return_message += "ERROR: 既に登録されています！"
                else:
                    return_view = ui.View()  # Viewインスタンスを作成
                    button_R = self.RegisterNameOKButton(
                        label='OK',
                        style=discord.ButtonStyle.green,
                        custom_id=str(message.author) + "_register_name",
                        spread_sheet=self.spread_content,
                        register_name=str(register_name),
                        register_id=registrant_id,
                        is_meow=is_meow)  # Buttonインスタンスを作成
                    if (is_meow):
                        return_message += f"{register_name}さんを登録しますかにゃ？"
                    else:
                        return_message += f"{register_name}さんを登録しますか？"
                    return_view.add_item(button_R)
                await message.channel.send(return_message, view=return_view)
                return

            elif splited_message[0] == 'csv' and str(message.author) in super_user:

                self.spread_content.get_name_len()
                all_spread_data = self.spread_content.get_cells(
                    self.spread_content.x_pos, self.spread_content.y_pos, self.spread_content.x_len, self.spread_content.name_len)
                header = self.spread_content.get_cells(
                    self.spread_content.x_pos + 1, 1, self.spread_content.x_len, 1)

                """
                all_spread_data = self.spread_content.ss.get('B3:AL25')
                header = self.spread_content.ss.get('C1:AL1')
                """

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
                if (is_meow):
                    return_message += "送信しましたにゃ"
                else:
                    return_message += "送信しました"
                await message.channel.send(return_message,
                                           file=discord.File(
                                               "output.csv", 'output.csv'))
                return

            elif splited_message[0] == "生存確認" or splited_message[
                    0] == "こんにちは！" or splited_message[0] == "こんにちはにゃ！":
                if (is_meow):
                    return_message += "こんにちはにゃ！"
                else:
                    return_message += "こんにちは！"
                await message.channel.send(return_message)
                await message.remove_reaction("🤔", message.guild.me)
                await message.add_reaction("🥰")
                return

            elif contains_any_substring(splited_message[0], meowmeow_input) and len(splited_message) == 1:
                return_message += random.choice(meowmeow_output)
                return_message += random.choice(["🐾", "🐈", "", ""])
                await message.channel.send(return_message)
                await message.remove_reaction("🤔", message.guild.me)
                await message.add_reaction("🐈")
                return

            elif splited_message[0] == '名前変更' and len(splited_message) == 2:
                if (not self.spread_content.name_exists(register_name)):
                    if (is_meow):
                        return_message += "えらー: 指定の名前の人物は見つかりませんでしたにゃ"
                    else:
                        return_message += "ERROR: 指定の名前の人物は見つかりませんでした。"
                elif (self.spread_content.name_exists(splited_message[1])):
                    if (is_meow):
                        return_message += "えらー: 名前が被っていますにゃ！"
                    else:
                        return_message += "ERROR: 名前が被っています！"
                else:
                    return_view = ui.View()  # Viewインスタンスを作成
                    button_RN = self.RenameOKButton(
                        label='OK',
                        style=discord.ButtonStyle.green,
                        custom_id=str(message.author) + "_register_name",
                        spread_sheet=self.spread_content,
                        old_name=str(register_name),
                        new_name=splited_message[1],
                        is_meow=is_meow)  # Buttonインスタンスを作成

                    if (is_meow):
                        return_message += f"{register_name}さんの名前を{splited_message[1]}に変更しますかにゃ？"
                    else:
                        return_message += f"{register_name}さんの名前を{splited_message[1]}に変更しますか？"
                    return_view.add_item(button_RN)

            elif splited_message[0] == '名前削除' and len(splited_message) >= 2:
                if (str(message.author) in super_user):
                    cell_pos = self.spread_content.find_name_pos(
                        splited_message[1]) - 3

                    if (cell_pos < 0):
                        if (is_meow):
                            return_message += "えらー: 名前が見つかりませんでしたにゃ"
                        else:
                            return_message += "ERROR: 名前が見つかりませんでした。"
                    else:
                        return_view = ui.View()  # Viewインスタンスを作成
                        button_D = self.NameDeleteOKButton(
                            label='OK',
                            style=discord.ButtonStyle.green,
                            custom_id=str(message.author) + "_delete",
                            spread_sheet=self.spread_content,
                            delete_name=splited_message[1],
                            is_meow=is_meow)  # Buttonインスタンスを作成

                        if (is_meow):
                            return_message += f"{splited_message[1]}さんを削除しますかにゃ？"
                        else:
                            return_message += f"{splited_message[1]}さんを削除しますか？"
                        return_view.add_item(button_D)
                else:
                    if (is_meow):
                        return_message += "えらー: 権限がありませんにゃ！"
                    else:
                        return_message += "ERROR: 権限がありません！"

            else:
                return_message, return_view = self.analysis_point_spreadsheet(
                    register_name, message, is_agent, is_meow)  # ポイント解析

            if (return_message != ""):
                print(return_message)
                await message.channel.send(return_message, view=return_view)
            else:
                await message.remove_reaction("🤔", message.guild.me)
        except Exception as e:
            error_message = traceback.format_exc()
            await message.channel.send(f"予期しないエラーが発生しました: {e}\n"+error_message)
            print(f"予期しないエラーが発生しました: {e}\n"+error_message)

    def analysis_point_spreadsheet(self, register_name, message, is_agent, is_meow):
        return_message = ""
        return_view = None
        print(message.content)
        messagePointContainer = MessagePointContainer(message.content)
        point_set_list = messagePointContainer.get_point_set_list()
        is_name_exists = self.spread_content.name_exists(register_name)
        if (len(point_set_list) > 0):
            if (not is_name_exists):
                if (is_agent):
                    if (is_meow):
                        return_message = f"{message.author.mention}  えらー: 存在しない名前ですにゃ！"
                    else:
                        return_message = f"{message.author.mention}  ERROR: 存在しない名前です！"
                else:
                    if (is_meow):
                        return_message += "えらー: 名前がスプレッドシートに登録されていませんにゃ！「名前登録」と送信すると名前を登録できますにゃ"
                    else:
                        return_message += "ERROR: あなたの名前がスプレッドシートに登録されていません！「名前登録」と送信すると名前を登録できます。"
                return return_message, None
            else:
                is_registered_name, unupdated_list = self.spread_content.find_point(
                    register_name, point_set_list)

                if (len(unupdated_list) == 0 and len(point_set_list) > 0):
                    if (is_meow):
                        return_message = f"{message.author.mention}   最新の状態ですにゃ！"
                    else:
                        return_message = f"{message.author.mention}   最新の状態です！"

                elif (is_registered_name):
                    if (is_meow):
                        return_message = f"{message.author.mention} 以下の内容でよいなら更新をポチっと押してくださいにゃ\n"
                    else:
                        return_message = f"{message.author.mention} 以下の内容でよいなら更新をポチっと押してください\n"
                    return_message += register_name + "さん\n"
                    for unupdated_point in unupdated_list:
                        return_row_message = ""
                        return_row_message = unupdated_point[
                            "element"] + unupdated_point[
                                "level"] + "\t" + unupdated_point[
                                    "registered_point"] + "→" + unupdated_point[
                                        "point"] + "\n"
                        return_message += return_row_message

                    return_view = ui.View()  # Viewインスタンスを作成
                    button1 = self.PointOKButton(
                        label='更新',
                        style=discord.ButtonStyle.green,
                        custom_id=str(message.author) + "_ok",
                        spread_sheet=self.spread_content,
                        unupdated_list=unupdated_list,
                        is_meow=is_meow)  # Buttonインスタンスを作成

                    return_view.add_item(button1)  # ViewにButtonを追加
                return return_message, return_view
        else:
            return return_message, None

    async def on_timeline_message(self, message):
        try:
            await message.add_reaction("🤔")
            is_meow = contains_any_substring(
                str(message.content), meowmeow_input)
            tl_author_other = self.mongo_db.distinct_tl("author")

            return_message = f"{message.author.mention} "
            return_view = None
            self.messageTimelineContainer = MessageTimelineContainer(
                message, tl_author_other)
            if (self.messageTimelineContainer.message_type == "TL"):
                if (is_meow):
                    return_message += "以下のタイムラインを登録しますかにゃ？\n"
                else:
                    return_message += "以下のタイムラインを登録しますか？\n"

                return_message += self.messageTimelineContainer.tl_string

                return_view = ui.View()  # Viewインスタンスを作成
                button_TO = self.TLOKButton(
                    label='OK',
                    style=discord.ButtonStyle.green,
                    custom_id=str(message.author) + "_ok",
                    mongoDB=self.mongo_db,
                    messageTimelineContainer=self.messageTimelineContainer,
                    is_meow=is_meow)  # Buttonインスタンスを作成

                return_view.add_item(button_TO)
            elif (self.messageTimelineContainer.message_type == "please"):

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

                send_text = ""
                for query in search_query_list:
                    if (query != None):
                        send_text += query+" "

                if (send_text != ""):
                    if (is_meow):
                        send_text += "でけんさくしたにゃ\n"
                    else:
                        send_text += "の条件で検索しました\n"

                if (is_meow):
                    return_message += send_text+"みたいタイムラインをえらんでにゃ\n"
                else:
                    return_message += send_text+"表示したいタイムラインを選択してください\n"

                return_view = ui.View()  # Viewインスタンスを作成
                list_TS = self.TLSearchList(
                    custom_id=str(message.author) + "_ts",
                    mongoDB=self.mongo_db,
                    messageTimelineContainer=self.messageTimelineContainer,
                    options=options,
                    is_meow=is_meow)  # Buttonインスタンスを作成

                return_view.add_item(list_TS)

            elif (self.messageTimelineContainer.message_type == "delete"):
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

                send_text = ""
                for query in search_query_list:
                    if (query != None):
                        send_text += query+" "

                if (send_text != ""):
                    if (is_meow):
                        send_text += "でけんさくしたにゃ\n"
                    else:
                        send_text += "の条件で検索しました\n"

                if (is_meow):
                    return_message += send_text+"みたいタイムラインをえらんでにゃ\n"
                else:
                    return_message += send_text+"表示したいタイムラインを選択してください\n"

                return_view = ui.View()  # Viewインスタンスを作成
                list_TS = self.TLSearchList(
                    custom_id=str(message.author) + "_ts",
                    mongoDB=self.mongo_db,
                    messageTimelineContainer=self.messageTimelineContainer,
                    options=options,
                    is_meow=is_meow)  # listインスタンスを作成

                return_view.add_item(list_TS)

            elif (self.messageTimelineContainer.message_type == "none"):
                if (is_meow):
                    return_message += random.choice(meowmeow_output)
                    return_message += random.choice(["🐾", "🐈", "", ""])

            if (return_message != f"{message.author.mention} "):
                await message.channel.send(return_message, view=return_view)
            else:
                await message.remove_reaction("🤔", message.guild.me)
        except Exception as e:
            error_message = traceback.format_exc()
            await message.channel.send(f"予期しないエラーが発生しました: {e}\n"+error_message)
            print(f"予期しないエラーが発生しました: {e}\n"+error_message)

    class PointOKButton(ui.Button):

        def __init__(self,
                     *,
                     label='OK',
                     spread_sheet: SpreadContent,
                     unupdated_list: list,
                     is_meow: bool,
                     **kwargs):
            self.spread_sheet = spread_sheet
            self.unupdated_list = unupdated_list
            self.is_meow = is_meow
            super().__init__(label=label, **kwargs)

        async def callback(self, interaction: Interaction):

            try:
                await interaction.response.defer(thinking=True)

                self.spread_sheet.register_point(self.unupdated_list)
                if (self.is_meow):
                    send_message = "更新しましたにゃ！\n"
                else:
                    send_message = "更新しました！\n"

                for unupdated_point in self.unupdated_list:
                    return_row_message = unupdated_point[
                        "element"] + unupdated_point[
                            "level"] + "\t" + unupdated_point[
                                "registered_point"] + "→" + unupdated_point[
                                    "point"] + "\n"
                    send_message += return_row_message
                await interaction.followup.send(content=send_message)
                self.view.stop()
            except Exception as e:
                error_message = traceback.format_exc()
                await interaction.followup.send(content=f"予期しないエラーが発生しました: {e}\n"+error_message)
                print(f"予期しないエラーが発生しました: {e}\n"+error_message)

    class NameDeleteOKButton(ui.Button):

        def __init__(self,
                     *,
                     label='OK',
                     spread_sheet: SpreadContent,
                     delete_name: str,
                     is_meow: bool,
                     **kwargs):
            self.spread_sheet = spread_sheet
            self.delete_name = delete_name
            self.is_meow = is_meow
            super().__init__(label=label, **kwargs)

        async def callback(self, interaction: Interaction):
            try:
                await interaction.response.defer(thinking=True)
                send_message = self.spread_sheet.delete_name(
                    self.delete_name, is_meow=self.is_meow)

                await interaction.followup.send(content=send_message)
                self.view.stop()
            except Exception as e:
                error_message = traceback.format_exc()
                await interaction.followup.send(content=f"予期しないエラーが発生しました: {e}\n"+error_message)
                print(f"予期しないエラーが発生しました: {e}\n"+error_message)

    class RegisterNameOKButton(ui.Button):

        def __init__(self,
                     *,
                     label='OK',
                     spread_sheet: SpreadContent,
                     register_name: str,
                     register_id: str,
                     is_meow: bool,
                     **kwargs):
            self.spread_sheet = spread_sheet
            self.register_name = register_name
            self.register_id = register_id
            self.is_meow = is_meow
            super().__init__(label=label, **kwargs)

        async def callback(self, interaction: Interaction):
            try:
                await interaction.response.defer(thinking=True)
                send_message = self.spread_sheet.registered_name(
                    self.register_name, self.register_id, is_meow=self.is_meow)

                await interaction.followup.send(content=send_message)
                self.view.stop()
            except Exception as e:
                error_message = traceback.format_exc()
                await interaction.followup.send(content=f"予期しないエラーが発生しました: {e}\n"+error_message)
                print(f"予期しないエラーが発生しました: {e}\n"+error_message)

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

    class TLOKButton(ui.Button):
        def __init__(self,
                     *,
                     label='OK',
                     mongoDB: MongoDB,
                     messageTimelineContainer: MessageTimelineContainer,
                     is_meow: bool,
                     **kwargs):
            self.is_meow = is_meow
            self.mongoDB = mongoDB
            self.messageTimelineContainer = messageTimelineContainer
            super().__init__(label=label, **kwargs)

        async def callback(self, interaction: Interaction):
            try:
                await interaction.response.defer(thinking=True)
                send_message = self.mongoDB.insert_tl(
                    self.messageTimelineContainer.json_string)
                await interaction.followup.send(content=send_message)
            except Exception as e:
                error_message = traceback.format_exc()
                await interaction.followup.send(content=f"予期しないエラーが発生しました: {e}\n"+error_message)
                print(f"予期しないエラーが発生しました: {e}\n"+error_message)

    class TLSearchList(ui.Select):
        def __init__(self,
                     *,
                     mongoDB: MongoDB,
                     messageTimelineContainer: MessageTimelineContainer,
                     is_meow: bool,
                     **kwargs):
            super().__init__(**kwargs)
            self.is_meow = is_meow
            self.mongoDB = mongoDB
            self.messageTimelineContainer = messageTimelineContainer
            self.message_type = self.messageTimelineContainer.message_type

        async def callback(self, interaction: Interaction):
            try:
                await interaction.response.defer(thinking=True)
                send_message = ""
                selected_value = self.values[0]
                if (self.message_type == "please"):
                    send_message += "選択したタイムラインです。\n"
                    document = self.mongoDB.search_tl_id(
                        ObjectId(selected_value))
                    send_message += self.messageTimelineContainer.tl_all_printer(
                        document)
                elif (self.message_type == "delete"):
                    send_message += "削除しました。\n"
                    self.mongoDB.delete_tl(ObjectId(selected_value))

                await interaction.followup.send(content=send_message)
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
