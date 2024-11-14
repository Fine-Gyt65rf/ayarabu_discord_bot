import re

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