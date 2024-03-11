# PyPaperSearch
ウィンドウ内アイコン表示のため、app.icoを実行ファイルと同じフォルダに入れてください<br>
## Python開発環境(Rye)
rye init PyPaperSearch<br>
cd PyPaperSearch<br>
rye pin 3.10.13<br>
rye add requests PyQt5 feedparser python-Levenshtein pyinstaller<br>
rye sync<br>
.\\.venv\Scripts\activate<br>

## 実行ファイルの作成方法（exeファイルなど）
pyinstaller main.py --onefile --noconsole --icon=app.ico<br>
Windows, Mac, Linuxでコマンドは共通（実行ファイルの拡張子が違う）
