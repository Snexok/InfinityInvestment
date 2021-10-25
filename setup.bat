@echo off

:start
cls

pip install --upgrade pip

pip install -i https://test.pypi.org/simple/ --extra-index-url=https://pypi.org/simple/ tinkoff-invest-openapi-client
pip install python-telegram-bot --upgrade

pause
exit