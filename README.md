# TGbot_template
template for aiogram bot with postgres via async peewee

1. Склонировать репозиторий: 
```commandline
git clone https://github.com/Vladq770/voicee.git
```
2. Создать окружение `venv``:
```commandline
python -m venv venv
```
3. Активировать окружение:
```commandline
.\venv\Scripts\activate
```
4. Установить зависимости:
```commandline
poetry install --no-root
```
5. Создать файл `.env`, скопировать в него содержимое из [template.env](template.env), отредактировать под своё окружение.

## Тесты и линтеры

- Запустить black: `black .`
- Запустить pytest: `pytest`

## Запуск приложения в докере
```commandline
docker-compose build 
docker-compose up -d
```