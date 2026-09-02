#!/bin/zsh
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
cd "$(dirname "$0")"
PORT=4488
lsof -ti tcp:$PORT | xargs kill -9 2>/dev/null
python3 server.py $PORT &
sleep 2
open "http://127.0.0.1:$PORT/"
wait
