#!/bin/bash

echo "Activating virtual environment..."
source ./venv/bin/activate

export API_TOKEN='0000000000:000000000-0000000000000000000000000'
export DATABASE_URL='mysql+pymysql://root:123123@localhost/123123'
echo "Starting the bot..."
python3 main.py

echo "Press any key to continue..."
read -n 1 -s
