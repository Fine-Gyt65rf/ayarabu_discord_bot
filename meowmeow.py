import jaconv
import random
import re

def contains_any_substring(main_string, substrings):
    return any(substring in main_string for substring in substrings)

class MeowMeow:
    def __init__(self):

        meowmeow_input_raw = ["にゃ" ,"みゃ" ,"ニャ" , "ミャ", "シャー"]

        meowmeow_input = meowmeow_input_raw
        meowmeow_input += ["🐱", "🐈", "🐾", "😺", "😸", "😹", "😻", "😼", "😽", "🙀", "😿", "😾"]

        meowmeow_output_raw = [
            "ごろごろ", "にゃっ", "にゃー", "にゃーん", "にゃーお", "にゃん", "にゃおーん", "にゃんにゃん", "にゃお",
            "にゃにゃ", "にゃにゃっ", "にゃにゃにゃ", "にゃおー", "にゃにゃーん", "にゃーご", "なーん",
        ]

        meowmeow_output = meowmeow_output_raw
        meowmeow_output += [meow.replace("に", "み") for meow in meowmeow_output]
        meowmeow_output += [jaconv.hira2kata(meow) for meow in meowmeow_output]
        meowmeow_output += [meow.replace("ー", "～") for meow in meowmeow_output]
        meowmeow_output += meowmeow_input_raw
        meowmeow_output += [str(meow) + "！" for meow in meowmeow_output]

        self.meowmeow_input=meowmeow_input
        self.meowmeow_output=meowmeow_output
        
        meowmeow_chance = ["ました","ません","です","います","ますか","でした","います","できます","ください","下さい",]

    def meowmeow_check(self,text):
        return(contains_any_substring(text, self.meowmeow_input))
        
    def meowmeow_return(self):
        meowmeow_message = ""
        meowmeow_message += random.choice(self.meowmeow_output)
        meowmeow_message += random.choice(["🐾", "🐈", "", ""])
        return return_message

    def meowmeow_accent(self,text):
        # 猫語の語尾フレーズ
        cat_phrases = ["にゃ", "にゃん", "みゃあ", "だにゃ", "だにゃん"]

        # 定型フレーズを猫語に変換
        def convert_greeting(match):
            phrase = match.group(1)
            punctuation = match.group(2) or ""  # 句読点があればそのまま保持
            # すでに猫語が付加されていない場合のみ、にゃ・にゃんを追加
            if not re.search(r'(にゃ|にゃん|みゃあ|だにゃ|だにゃん)$', phrase):
                return phrase + random.choice(["にゃ", "にゃん"]) + punctuation
            return phrase + punctuation

        # 変換したい定型フレーズ
        greetings = ['こんにちは', 'こんばんは', 'ありがとう', 'おはよう', 'さようなら']

        # 定型フレーズを猫語に変換
        for greeting in greetings:
            text = re.sub(f'({greeting})([、。！？])?', convert_greeting, text)

        # 通常の語尾変換（「です」「ます」「だ」など）
        def convert_tail(match):
            word = match.group(1)
            punctuation = match.group(2) or ""
            # すでに猫語が含まれている語尾はそのまま保持
            if not re.search(r'(にゃ|にゃん|みゃあ|だにゃ|だにゃん)$', word):
                return word + random.choice(cat_phrases) + punctuation
            return word + punctuation

        # 語尾（「です」「ます」「だ」など）を猫語に変換
        text = re.sub(r'(です|ます|だ|よ|ね|わ|か)([、。！？])?', convert_tail, text)

        # その他の表現（「ない」を「にゃい」に、「する」を「するにゃ」に）
        text = re.sub(r'ない', 'にゃい', text)
        text = re.sub(r'する', 'するにゃ', text)

        # 文末が既に猫語の場合を除き、文末に猫語の響きを追加
        if not re.search(r'(にゃ|にゃん|みゃあ|だにゃ|だにゃん)$', text):
            text += random.choice(["にゃ〜", "にゃん〜", "みゃあ〜", "だにゃ〜"])

        return text

# テスト用の文章
meowmeow=MeowMeow()
sample_text = "こんにちは！今日は良い天気ですね。お散歩に行きますか？"
converted_text = meowmeow.meowmeow_accent(sample_text)
print("猫語変換後:", converted_text)