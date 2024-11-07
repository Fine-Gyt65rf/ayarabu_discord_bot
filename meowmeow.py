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
        

        # 猫語の語尾フレーズ
        self.cat_phrases = ["にゃ", "ニャ","にゃ～", "ニャ～"]

        # 変換対象の語尾や命令形
        self.tails = ["です", "ます", "だ", "よ", "ね", "わ", "か", "する", "ください", "した"]

        # 変換対象の語尾リストを正規表現に変換
        self.tail_pattern = r'(' + '|'.join(self.tails) + r')\b([、。!?！？]?)'

        # 猫語語尾の正規表現パターン
        self.cat_phrase_pattern = r'(' + '|'.join(self.cat_phrases) + r')$'

    def convert_katakana_to_hiragana(self, text):
        # テキスト内のカタカナをひらがなに変換
        return jaconv.kata2hira(text)

    def meowmeow_check(self,text):
        return(contains_any_substring(text, self.meowmeow_input))
        
    def meowmeow_return(self):
        meowmeow_message = ""
        meowmeow_message += random.choice(self.meowmeow_output)
        meowmeow_message += random.choice(["🐾", "🐈", "", ""])
        return meowmeow_message

    def meowmeow_accent(self,text,is_meow):
        
        if(is_meow):
            # カタカナをひらがなに変換
            text = self.convert_katakana_to_hiragana(text)

            # 定型フレーズを猫語に変換
            def convert_greeting(match):
                phrase = match.group(1)
                punctuation = match.group(2) or ""  # 句読点があればそのまま保持
                # すでに猫語が付加されていない場合のみ、にゃ・にゃんを追加
                if not re.search(self.cat_phrase_pattern, phrase):
                    return phrase + random.choice(self.cat_phrases) + punctuation
                return phrase + punctuation

            # 変換したい定型フレーズ
            greetings = ['こんにちは', 'こんばんは', 'ありがとう', 'おはよう', 'さようなら']

            # 定型フレーズを猫語に変換
            for greeting in greetings:
                text = re.sub(f'({greeting})([、。!?！？]?)', convert_greeting, text)

            # 通常の語尾変換と命令形の変換
            def convert_tail(match):
                word = match.group(1)
                punctuation = match.group(2) or ""
                # すでに猫語が含まれている語尾はそのまま保持
                if not re.search(self.cat_phrase_pattern, word):
                    return word + random.choice(self.cat_phrases) + punctuation
                return word + punctuation

            # 正規表現パターンを使って語尾変換を実行
            text = re.sub(self.tail_pattern + r'$', convert_tail, text)
            text = re.sub(self.tail_pattern, convert_tail, text)

            # その他の表現（「ない」を「にゃい」に、「する」を「するにゃ」に）に単語境界を追加
            text = re.sub(r'(?<!にゃ)ない\b', 'にゃい', text)  # すでに「にゃい」になっている場合は変換しない
            text = re.sub(r'(?<!にゃ)する\b', 'するにゃ', text)  # すでに「するにゃ」になっている場合は変換しない

        return text

def main():
    # テスト用の文章
    meowmeow=MeowMeow()
    sample_text = "表示したいタイムラインを選択してください\n"
    converted_text = meowmeow.meowmeow_accent(sample_text,True)
    print("猫語変換後:", converted_text)


if __name__ == "__main__":
    main()