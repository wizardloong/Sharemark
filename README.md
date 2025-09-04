# Sharemark

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![Made with Python](https://img.shields.io/badge/Python-3.11-blue.svg)]()
[![Chrome Web Store](https://img.shields.io/badge/Chrome_Extension-coming_soon-orange.svg)]()

🔮 **Sharemark** — это расширение для браузера, которое позволяет делиться папками с закладками через одноразовые ссылки.  
Просто выберите папку → сгенерируйте ссылку → поделитесь ей в один клик.  
Никакой регистрации, никакой синхронизации аккаунтов, только удобство и скорость.

👉 Официальный сайт: [getsharemark.com](https://getsharemark.com)


## ✨ Возможности

- 📂 Делитесь целыми папками закладок, а не отдельными ссылками  
- 🔗 Одноразовые безопасные ссылки  
- 🪄 Максимально простой UX — два клика и всё готово  
- 🚀 Минимум инфраструктуры (не требует аккаунта)  
- 🔒 Конфиденциальность и безопасность  


## 📦 Установка

### Google Chrome (скоро в Web Store)
1. Перейдите на страницу расширения в [Chrome Web Store](#) _(coming soon)_  
2. Нажмите **Установить**  

### Локальная установка (для разработчиков)
1. Склонируйте репозиторий  

```bash
   git clone https://github.com/username/sharemark.git
   cd sharemark/extension
````

2. Откройте **Chrome → Расширения → Режим разработчика → Загрузить распакованное расширение**
3. Укажите путь к папке `extension/`

## 🚀 Запуск backend

```bash
make build && make up
```

Backend поднимется в Docker вместе с MySQL, Redis и RabbitMQ.

## 🗂️ Миграции

```bash
make migrate
```

## 🧪 Тестирование

```bash
git checkout test
git pull
make build
make reup
make test
```

## 📂 Структура проекта

```
.
├── app                     # Бэкенд приложение
│   ├── api.py              # API эндпоинты
│   ├── data_storage.py     # Хаб временных хранилищ
│   ├── infrastructure      # Всё, что помогает проекту
│   │   ├── consumers       # Консьюмеры RabbitMQ
│   │   ├── helpers         # Вспомогательные функции
│   │   ├── middlewares     # Посредники
│   │   └── rabbitmq.py     # Инициализация брокера сообщений
│   ├── main.py             # Точка входа
│   ├── models              # Сущности
│   ├── portal.py           # Эндпоинты сайта
│   ├── public              # Публичные файлы сайта
│   │   ├── static          # Статика (css, js, images)
│   │   └── templates       # HTML-шаблоны
│   ├── repos               # Репозитории для работы с БД
│   ├── schemas.py          # Схемы запросов
│   ├── storage             # Классы работы с хранилищами
│   ├── tests               # Тесты
│   └── websocket.py        # WebSocket эндпоинты
├── env                     # Docker-окружение и конфиги
│   ├── docker-compose.yml  
│   ├── Dockerfile          
│   ├── migrations          
│   ├── mysql               
│   ├── rabbitmq            
│   ├── redis               
│   └── requirements.txt    
├── extension               # Код браузерного расширения
│   ├── background.js       
│   ├── manifest.json
│   ├── popup.html
│   └── popup.js
├── Makefile                # Основные команды
└── README.md               # Этот файл
```

## 🤝 Контрибьютинг

Будем рады PR и issue!

1. Сделайте fork
2. Создайте ветку `feature/my-feature`
3. Отправьте Pull Request


---

```
        /\    
       /__\        .-"        "-. 
      /|  |\      /              \ 
     /_|__|_\     |,  .-.  .-.  ,| 
      /::::\      | )(_o/  \o_)( |   Sharemark
      `====`      |/     /\     \|   "Magic of bookmarks"
                  (_     ^^     _) 
                   \__|IIIIII|__/ 
                    | \IIIIII/ | 
                    \          / 
                     `--------`
```
