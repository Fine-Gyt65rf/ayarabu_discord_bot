import os
import discord
import traceback
import asyncio
from bot.my_bot import MyBot
from bot.keep_alive import keep_alive


super_user = ["fine4139", "ayalovex0001", "liankuma", "kujirakusu_07611", "kiyoka6639"]
bot = MyBot(intents=discord.Intents.all())

# Botトークンの環境変数を確認
TOKEN = os.environ.get('TOKEN')
if not TOKEN:
    print("Error: TOKEN environment variable not set.")
    exit(1)

# ----- メインの実行処理 -----
async def main():
    """
    非同期でボットとウェブサーバーを同時に起動するメイン関数。
    """
    # Discordボットのタスクを起動
    discord_task = asyncio.create_task(bot.start(TOKEN))
    
    # ウェブサーバーのタスクを起動
    # keep_alive() が非同期関数でない場合はそのまま呼び出す
    keep_alive() # keep_alive()がポートをリスンする非同期サーバーではない場合
    
    # keep_alive() が非同期サーバーを起動する関数であれば、
    # asyncio.create_task(...) を使用してタスクとして実行する
    # 例: web_task = asyncio.create_task(keep_alive_async())

    print("起動成功: Discordボットとウェブサーバーを起動しました。")
    
    # 両方のタスクが終了するまで待機
    # 通常、ボットのタスクは終了しないため、awaitは不要
    await discord_task
    
    # 以下はウェブサーバーのタスクもawaitする場合
    # await asyncio.gather(discord_task, web_task)


# プロセス実行時のエントリーポイント
if __name__ == "__main__":
    try:
        # asyncio.run()を使って非同期メイン関数を実行
        asyncio.run(main())
    except discord.LoginFailure:
        print("起動失敗: 無効なトークンが提供されました。")
        traceback.print_exc()
        # Dockerコンテナを終了
        os.system("kill 1")
    except Exception as e:
        print(f"起動失敗: 予期せぬエラーが発生しました。{e}")
        traceback.print_exc()
        # Dockerコンテナを終了
        os.system("kill 1")