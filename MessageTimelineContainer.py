import re
import datetime
import time

class MessageTimelineContainer:
    def __init__(self, message, tl_author_other):
        self.message = message
        self.content = self.message.content
        self.author_name = self.message.author.display_name

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
                self.search_type_dict["author"] = self.author_name
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