#!/bin/bash
# スクリプトのあるディレクトリに移動
cd "$(dirname "$0")"

# 仮想環境があれば有効化
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: 仮想環境(venv)が見つかりません。セットアップを行ってください。"
    exit 1
fi

# 引数をそのままPythonスクリプトに渡して実行
python main.py "$@"
