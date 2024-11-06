# coding: utf-8
import configparser as cp

class ConfigInitializer:

    def __init__(self,section_name):
        #ConfigParserオブジェクトを生成
        self.config = cp.ConfigParser()
        self.section_name = section_name
        #設定ファイル読み込み
        self.config.read('config.ini')
        self.config.read()
        
    def read(self,section_name,object_name):
        arr = json.loads(self.config.get(section_name,object_name))
