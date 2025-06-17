import json
from pymongo import MongoClient
import traceback
import os


class MongoDB:
    def __init__(self):
        # MongoDB Atlasから取得した接続文字列を使用
        self.client = MongoClient(os.environ["MONGO_CLIENT"])
        self.db = self.client["ayarabu"]
        self.collection = self.db["timeline"]  # 'collection'も任意の名前でOK

    def distinct_tl(self, things):
        # コレクション内のすべての著者を集める
        things_list = self.collection.distinct(things)
        return things_list

    def insert_tl(self, json_data):
        try:
            self.collection.insert_one(json_data)
            return "登録しました！"
        except Exception as e:
            error_message = f"予期しないエラーが発生しました: {e}\n" + traceback.format_exc()
            print(error_message)
            return error_message

    def delete_tl(self, id):
        query = {"_id": id}
        self.collection.delete_one(query)

    # enemy_type_dict={"attack_type":None,"enemy_element":None,"enemy_level":None,"point":"3"}
    def search_tl(self, element=None, level=None, attack_type=None, point=None, author=None, see_all=None):

        documents = []
        # クエリを作成
        query = {
            "$and": [
            ]
        }

        if (attack_type != None):
            query["$and"].append({"$or":
                                  [
                                      # フィールドAがvalue1に一致する
                                      {"attack_type": attack_type},
                                      # またはフィールドAがvalue2に一致する
                                      {"attack_type": None}
                                  ]
                                  })
        if (point != None):
            query["$and"].append({"point": point})  # フィールドBがvalue2に一致する

        if (element != None):
            query["$and"].append({"enemy_element": element})

        if (level != None):
            query["$and"].append({"enemy_level": level})

        if (author != None):
            query["$and"].append({"author": author})

        if (see_all != None or see_all == False):
            query["$and"].append({"visibility": True})

        documents = list(self.collection.find(query))
        return documents

    def search_tl_id(self, id):
        document = self.collection.find_one({"_id": id})
        return document

    def set_visibility_tl(self, id, visibility):
        # 更新条件と修正内容
        filter_query = {"_id": id}   # 更新対象の条件
        update_query = {'$set': {'visibility': visibility}}  # 更新内容
        # 一致する最初のドキュメントを更新
        result = self.collection.update_one(filter_query, update_query)
