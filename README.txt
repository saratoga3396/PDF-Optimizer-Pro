動作させるための手順:

1. ターミナルで仮想環境を有効にします (必須)
   source venv/bin/activate

2. ツールを実行します
   python main.py samples/IMG_001.pdf

   (フォルダごと処理する場合)
   python main.py /path/to/folder

   (テスト実行・保存なし)
   python main.py samples/IMG_001.pdf --dry-run
