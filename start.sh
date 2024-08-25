#/bin/sh

SESSION_NAME=`pwd | grep -o '[^/]*$'`

if ! screen -list | grep -E "^\s*[0-9]+\.${SESSION_NAME}\s+" > /dev/null; then
    echo "Скрипт '$SESSION_NAME' не запущен. Запускаю..."
    screen -S "$SESSION_NAME" ./START.sh
else
    echo "Сессия $SESSION_NAME уже существует. Подключаюсь к ней..."
    screen -r "$SESSION_NAME"
fi
