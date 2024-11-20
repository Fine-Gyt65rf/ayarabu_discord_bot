from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload
import gspread
import datetime
import json
import os

levels = ["180", "190", "200", "250", "275", "300", "325"]


class SpreadContent:

    def __init__(self):
        self.spreadsheet_url = os.environ["SPREADSHEETS_URL"]
        # スコープの定義
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        # 認証情報を読み込む
        service_account_info = json.loads(os.environ["SPREADSHEETS_JSON"])
        credentials = Credentials.from_service_account_info(
            service_account_info, scopes=scopes)
        self.gc = gspread.authorize(credentials)
        self.spreadsheet = self.gc.open_by_url(self.spreadsheet_url)
        self.ss = self.spreadsheet.worksheet("戦力表")

        self.x_len = 2+len(levels)*5
        self.y_len = 23
        self.x_pos = 2
        self.y_pos = 3
        self.name_len = self.get_name_len()

    def register_point(self, unupdated_list):
        for registering_point in unupdated_list:
            if (registering_point["point"] != "-"):
                self.ss.update_cell(registering_point["cell_pos"][1],
                                    registering_point["cell_pos"][0],
                                    int(registering_point["point"]))
            else:
                self.ss.update_cell(registering_point["cell_pos"][1],
                                    registering_point["cell_pos"][0], str(""))

        dt_now = datetime.datetime.now()
        self.ss.update_cell(1, 2, dt_now.strftime('%Y年%m月%d日 %H:%M:%S'))
        print("書き込み終了")

    def get_name_len(self):
        ss_name_list = self.ss.col_values(2)
        ss_name_list = ss_name_list[2:ss_name_list.index(".")]
        self.y_len = len(ss_name_list)
        self.name_len = len([a for a in ss_name_list if a != ''])
        return self.name_len

    def name_exists(self, name):
        ss_name_list = self.read_name()
        self.get_name_len()
        return name in ss_name_list

    def id_exists(self, id):
        ss_id_list = self.read_id()
        self.get_name_len()
        return id in ss_id_list

    def read_name(self):
        ss_name_list = self.ss.col_values(2)
        ss_name_list = ss_name_list[2:ss_name_list.index(".")]
        return ss_name_list

    def read_id(self):
        ss_id_list = self.ss.col_values(3)
        ss_id_list = ss_id_list[2:ss_id_list.index(".")]
        return ss_id_list

    def read_name_max_len(self):
        ss_name_list = self.ss.col_values(2)
        return ss_name_list.index(".")-2

    def convert_id_to_name(self, id):
        cell_pos = self.find_id_pos(id)
        ss_name_list = self.read_name()
        name = ss_name_list[cell_pos - 3]
        return name

    def convert_name_to_id(self, id):
        cell_pos = self.find_id_pos(id)
        ss_name_list = self.read_name()
        name = ss_name_list[cell_pos - 3]
        return name

    def find_name_pos(self, name):
        ss_name_list = self.read_name()
        cell_pos = self.find_index(ss_name_list, name)
        if (cell_pos == -1):
            pass
        else:
            cell_pos += 3
        return cell_pos

    def find_id_pos(self, id):
        ss_id_list = self.read_id()
        cell_pos = self.find_index(ss_id_list, id)
        if (cell_pos == -1):
            pass
        else:
            cell_pos += 3
        return cell_pos

    def read_spreadsheet(self, x, y):
        registered_point = self.ss.cell(row=y, col=x).value
        if (registered_point is None):
            registered_point = "-"
        return registered_point

    def find_index(self, lx, x):
        if x in lx:
            return lx.index(x)
        else:
            return -1

    def delete_name(self, name):
        self.get_name_len()
        all_spread_data = self.get_cells(
            self.x_pos, self.y_pos, self.x_len, self.name_len)
        cell_pos = self.find_name_pos(name) - self.y_pos
        removed_data = all_spread_data.pop(cell_pos)
        print("削除する人の名前：", name, "リムーブされた名前：", removed_data)
        all_spread_data.append([""]*(2+len(levels)*5))
        print(all_spread_data)

        if (cell_pos < 0):
            return_message = "ERROR: 名前が見つかりませんでした。"
        elif (removed_data[0] == name):  # 削除する人のインデックスと名前がちゃんと一致していた場合
            # update_cells(self, start_x, start_y, end_x, end_y, values)
            self.update_cells(self.x_pos, self.y_pos,
                              self.x_len, self.name_len, all_spread_data)
            dt_now = datetime.datetime.now()
            self.ss.update_cell(1, 2, dt_now.strftime('%Y年%m月%d日 %H:%M:%S'))
            return_message = f"{name}さんを削除しました。"
        else:
            return_message = "ERROR: 削除できませんでした。"
        return return_message

    def registered_name(self, name, id):
        is_registered_name = self.name_exists(name)
        if (is_registered_name):
            return_message = "ERROR: 既に登録されています！"
        else:
            y_pos = self.find_name_pos("")
            self.ss.update_cell(y_pos, 2, name)  # name
            self.ss.update_cell(y_pos, 3, id)  # name
            dt_now = datetime.datetime.now()
            self.ss.update_cell(1, 2, dt_now.strftime('%Y年%m月%d日 %H:%M:%S'))
            return_message = f"{name}さんを登録しました！"
        return return_message

    def rename_name(self, old_name, new_name):
        is_registered_name = self.name_exists(new_name)
        if (is_registered_name):
            return_message = "ERROR: 既に登録されています！"
        else:
            y_pos = self.find_name_pos(old_name)
            self.ss.update_cell(y_pos, 2, new_name)  # name
            dt_now = datetime.datetime.now()
            self.ss.update_cell(1, 2, dt_now.strftime('%Y年%m月%d日 %H:%M:%S'))
            return_message = f"{new_name}さんに変更しました！"
        return return_message

    def find_point(self, user_name, parsed_dict):

        base_cell_pos = 4
        element_cell_pos_dict = {"火": 0, "水": 1, "風": 2, "光": 3, "闇": 4}

        level_cell_pos_dict = {levels[i]: 5*i for i in range(len(levels))}
        """
        level_cell_pos_dict = {
            "180": 0,
            "190": 5,
            "200": 10,
            "250": 15,
            "275": 20,
            "300": 25,
            "325": 30,
        }
        """

        y_cell_pos = self.find_name_pos(user_name)

        if (y_cell_pos == 0):  # リストに未登録の名前
            return False, []
        else:
            unupdated_list = []
            for point_info in parsed_dict:
                x_cell_pos = base_cell_pos
                x_cell_pos += element_cell_pos_dict[point_info["element"]]
                x_cell_pos += level_cell_pos_dict[point_info["level"]]
                point_info["registered_point"] = self.read_spreadsheet(
                    x_cell_pos, y_cell_pos)
                point_info["cell_pos"] = (x_cell_pos, y_cell_pos)

                if (point_info["registered_point"] != point_info["point"]):
                    if point_info["point"] == "0":
                        point_info["point"] = "-"
                    unupdated_list.append(point_info)
            print(unupdated_list)
            return True, unupdated_list

    def col_num_to_letter(self, col_num):
        """列番号を列名に変換する関数。"""
        letter = ''
        while col_num > 0:
            col_num, remainder = divmod(col_num - 1, 26)
            letter = chr(65 + remainder) + letter
        return letter

    def update_cells(self, start_x, start_y, len_x, len_y, update_values):
        end_x = start_x+len_x-1
        end_y = start_y+len_y-1
        print(start_x, start_y, end_x, end_y)

        """セル範囲を整数で指定して、ワークシートにデータを書き込む関数。"""
        # 列番号を列名に変換
        start_cell = f'{self.col_num_to_letter(start_x)}{start_y}'
        end_cell = f'{self.col_num_to_letter(end_x)}{end_y}'

        # 範囲を文字列で指定
        cell_range = f'{start_cell}:{end_cell}'
        print(cell_range)
        # 更新処理
        self.ss.update(cell_range, update_values,
                       value_input_option='USER_ENTERED')

    def read_strong_attributes_cells(self, level):
        id_list=self.read_id()
        strong_attributes_dict={}
        level_index=levels.index(level)
        strong_attributes_x_pos = self.x_pos + 2 + 5*len(levels) + 1 + 5*len(levels) + 1 + 5*len(levels) + 1 + level_index

        strong_attributes_list = self.ss.col_values(strong_attributes_x_pos)
        strong_attributes_list = strong_attributes_list[2:strong_attributes_list.index(".")]
        
        attribute_list=["火","水","風","光","闇"]
        for i, strong_attributes in enumerate(strong_attributes_list):
            found_attribute = [char for char in strong_attributes if char in attribute_list]
            for j, attribute in enumerate(found_attribute):
                found_attribute[j] = "対" + attribute
            found_attribute += ["同盟在籍者"]
            if(len(id_list[i]) != 0):
                strong_attributes_dict[id_list[i]] = found_attribute 
        #print(strong_attributes_dict)
        return strong_attributes_dict

    def get_cells(self, start_x, start_y, len_x, len_y):
        end_x = start_x+len_x-1
        end_y = start_y+len_y-1

        """セル範囲を整数で指定して、ワークシートにデータを書き込む関数。"""
        # 列番号を列名に変換
        start_cell = f'{self.col_num_to_letter(start_x)}{start_y}'
        end_cell = f'{self.col_num_to_letter(end_x)}{end_y}'

        # 範囲を文字列で指定
        cell_range = f'{start_cell}:{end_cell}'

        # セル範囲を取得
        result = self.ss.get(cell_range)
        return result