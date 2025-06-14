from discord import ui, Interaction
from discord.ui import Button,Select,View
import discord
import traceback

class DynamicOkButton(Button):
    def __init__(self, bot, initiator_user_id, is_meow, action,**kwargs):
        self.bot = bot
        self.initiator_user_id = initiator_user_id
        self.is_meow = is_meow
        self.action = action  # 実行する関数
        self.kwargs = kwargs  # 必要な追加情報
        super().__init__(label="OK", style=discord.ButtonStyle.green)

    async def callback(self, interaction: Interaction):
        try:
            if interaction.user.name != self.initiator_user_id:
                pass
            else:
                # 動的に設定された処理を実行
                await interaction.response.defer(thinking=True)
                return_view = View()
                return_message, return_view = self.action(**self.kwargs)
                await interaction.followup.send(content=return_message, view=return_view)
        except Exception as e:
            error_message = traceback.format_exc()
            await interaction.followup.send(content=f"予期しないエラーが発生しました: {e}\n"+error_message)
            print(f"予期しないエラーが発生しました: {e}\n"+error_message)

class DynamicSelectMenu(Select):
    def __init__(self, bot, initiator_user_id, is_meow, action, options ,**kwargs):
        super().__init__(options = options)
        self.bot = bot
        self.initiator_user_id = initiator_user_id
        self.is_meow = is_meow
        self.action = action  # 実行する関数
        self.options = options
        self.kwargs = kwargs

    async def callback(self, interaction: Interaction):
        print(interaction.user, self.initiator_user_id)
        if interaction.user.name != self.initiator_user_id:
            pass
        else:
            try:
                await interaction.response.defer(thinking=True)
                return_view=View()
                return_message,return_view = self.action(self.values[0] , **self.kwargs)
                await interaction.followup.send(content=return_message, view=return_view)
            except Exception as e:
                error_message = traceback.format_exc()
                await interaction.followup.send(content=f"予期しないエラーが発生しました: {e}\n"+error_message)
                print(f"予期しないエラーが発生しました: {e}\n"+error_message)