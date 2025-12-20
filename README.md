
# 🛍️ RShop - Интернет-магазин с Telegram WebApp

Полнофункциональный интернет-магазин с интеграцией Telegram WebApp, построенный на современном стеке технологий: React + TypeScript (frontend) и FastAPI + SQLite + Aiogram (backend).

## 📋 Содержание

- [Описание](#-описание)
- [Архитектура](#-архитектура)
- [Технологический стек](#-технологический-стек)
- [Быстрый старт](#-быстрый-старт)
- [Настройка окружения](#-настройка-окружения)
- [Конфигурация Telegram бота](#-конфигурация-telegram-бота)
- [API документация](#-api-документация)
- [Структура базы данных](#-структура-базы-данных)
- [Тестирование](#-тестирование)
- [Деплой на сервер](#-деплой-на-сервер)
- [Разработка и улучшения](#-разработка-и-улучшения)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Описание

RShop — это современный интернет-магазин с полной интеграцией Telegram:
- **Telegram Bot** для управления заказами и админ-панелью
- **Telegram WebApp** для пользовательского интерфейса
- **REST API** для всех операций
- **Админ-панель** через Telegram бота
- **История заказов** и статистика пользователей
- **Уведомления** о новых заказах

---

## 🏗️ Архитектура

```
rshop/
├── backend/                    # Python backend
│   ├── admin/                  # Модульная админ-панель (Telegram)
│   │   ├── brands.py          # Управление брендами
│   │   ├── categories.py      # Управление категориями
│   │   ├── products.py         # Управление товарами
│   │   └── ...
│   ├── api_server.py          # FastAPI REST API
│   ├── main.py                # Telegram бот (aiogram)
│   ├── database.py            # SQLAlchemy ORM
│   ├── models.py              # Модели данных
│   ├── init_db.py             # Инициализация БД
│   ├── run_server.py          # Запуск API сервера
│   ├── order_handlers.py      # Обработка заказов
│   ├── telegram_notifications.py  # Уведомления в Telegram
│   ├── logging_config.py      # Настройка логирования
│   ├── config.py              # Конфигурация
│   ├── data/                  # SQLite база данных
│   ├── static/                # Статические файлы (изображения)
│   ├── logs/                  # Логи приложения
│   └── requirements.txt        # Python зависимости
│
└── frontend/                   # React frontend
    ├── src/
    │   ├── pages/             # Страницы приложения
    │   │   ├── Shop.tsx       # Главная страница магазина
    │   │   ├── Admin.tsx      # Админ-панель (веб)
    │   │   ├── Payment.tsx   # Страница оплаты
    │   │   └── NotFound.tsx   # 404 страница
    │   ├── components/
    │   │   ├── shop/          # Компоненты магазина
    │   │   ├── admin/         # Компоненты админки
    │   │   └── ui/            # UI компоненты (shadcn/ui)
    │   ├── hooks/             # React хуки
    │   │   ├── useCart.ts     # Управление корзиной
    │   │   └── useTelegramWebApp.ts  # Telegram WebApp
    │   ├── lib/               # Утилиты и API
    │   │   ├── api.ts         # API клиент
    │   │   ├── logger.ts      # Логирование
    │   │   └── telegram.ts    # Telegram утилиты
    │   ├── config/            # Конфигурация
    │   │   └── app.config.ts  # Настройки приложения
    │   └── types/              # TypeScript типы
    ├── public/                 # Статические файлы
    └── package.json            # Node.js зависимости
```

---

## 🛠️ Технологический стек

### Backend
- **Python 3.11+**
- **FastAPI** - современный веб-фреймворк
- **SQLAlchemy 2.0** - ORM для работы с БД
- **aiosqlite** - асинхронный драйвер SQLite
- **Aiogram 3.0** - Telegram Bot framework
- **Pydantic** - валидация данных
- **Uvicorn** - ASGI сервер
- **python-dotenv** - управление переменными окружения

### Frontend
- **React 18** - UI библиотека
- **TypeScript** - типизация
- **Vite** - сборщик и dev-сервер
- **React Router** - маршрутизация
- **TanStack Query** - управление состоянием сервера
- **shadcn/ui** - UI компоненты (Radix UI)
- **Tailwind CSS** - стилизация
- **Lucide React** - иконки

---

## 🚀 Быстрый старт

### Предварительные требования

- **Python 3.11+**
- **Node.js 18+** и npm
- **Telegram Bot Token** (для production режима)

### 1. Клонирование и установка

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd rshop

# Установите backend зависимости
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Установите frontend зависимости
cd ../frontend
npm install
```

### 2. Настройка переменных окружения

Создайте файл `.env` в директории `backend/`:

```env
BOT_TOKEN=ваш_telegram_bot_token
ADMIN_CHAT_IDS=-1234567890,-9876543210
STATIC_ROOT=./static
```

### 3. Инициализация базы данных

```bash
cd backend
python init_db.py
```

Это создаст:
- SQLite базу данных в `backend/data/shop.db`
- Тестовые бренды, категории и товары

### 4. Запуск приложения

#### Backend (API + Telegram Bot)

```bash
# В первом терминале - запуск API сервера
cd backend
python run_server.py
# API будет доступен на http://localhost:8000
```

```bash
# Во втором терминале - запуск Telegram бота
cd backend
python main.py
```

#### Frontend

```bash
cd frontend
npm run dev
# Frontend будет доступен на http://localhost:5173
```

### 5. Проверка работы

- **API Health Check**: http://localhost:8000/api/health
- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs (Swagger UI)

---

## ⚙️ Настройка окружения

### Режимы работы Frontend

Приложение поддерживает 3 режима работы (настраивается в `frontend/src/config/app.config.ts`):

#### 1. Production (`production`)
```typescript
APP_MODE = 'production'
```
- Требует запуск в Telegram WebApp
- Проверка Telegram ID пользователя
- Роль определяется по ID из `TELEGRAM_CONFIG.adminIds`

#### 2. Debug User (`debug-user`)
```typescript
APP_MODE = 'debug-user'
```
- Работает без Telegram
- Роль: пользователь
- Доступ к магазину, корзине, оформлению заказов

#### 3. Debug Admin (`debug-admin`)
```typescript
APP_MODE = 'debug-admin'
```
- Работает без Telegram
- Роль: администратор
- Полный доступ к админ-панели

### Переменные окружения Backend

| Переменная | Описание | Обязательная |
|------------|----------|--------------|
| `BOT_TOKEN` | Токен Telegram бота | Да |
| `ADMIN_CHAT_IDS` | ID чатов администраторов (через запятую) | Нет |
| `STATIC_ROOT` | Путь к директории статических файлов | Нет (по умолчанию: `./static`) |

---

## 🤖 Конфигурация Telegram бота

### 1. Создание бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям и получите токен бота
4. Сохраните токен в `.env` файл как `BOT_TOKEN`

### 2. Настройка Mini App

Этот проект рассчитан на работу через Telegram Mini App (WebApp, открывающийся в шторке). Чтобы пользователи видели одну кнопку «Открыть магазин» и попадали в нужный URL, настройте бот полностью:

1. Опубликуйте фронтенд на HTTPS-домене. Для тестов можно использовать бесплатный туннель (например, Cloudflare Tunnel) — главное, чтобы ссылка была доступна по HTTPS.
2. Откройте `backend/main.py` и обновите значение `mini_app_url` на ваш боевой адрес мини-приложения.
3. В [@BotFather](https://t.me/BotFather) последовательно выполните команды:
   - `/setdomain` — укажите домен мини-приложения (пример: `yourdomain.com` или адрес туннеля).
   - `/setmenubutton` → выберите своего бота → тип `Web App`.
   - Задайте название кнопки (подпись будет видеть пользователь, например, «Открыть магазин»).
   - Вставьте полный URL мини-приложения (например, `https://yourdomain.com` или `https://<random>.trycloudflare.com`).

> После этого в профиле бота появится единственная кнопка, ведущая в мини-приложение. Дополнительных reply-кнопок не требуется: при запуске `/start` бот отправит приветственное сообщение с той же ссылкой (см. `backend/main.py`).

### 3. Проверка Mini App

1. В Telegram откройте вашего бота и отправьте `/start`.
2. Убедитесь, что бот отвечает сообщением с упоминанием мини-приложения и кликабельной ссылкой.
3. Нажмите кнопку в меню бота. Проверьте, что мини-приложение запускается без ошибок и корректно подставляет данные пользователя.
4. Если ссылка не открывается:
   - Проверьте, что домен совпадает в настройках BotFather и в `mini_app_url`.
   - Убедитесь, что страница доступна по HTTPS и у сертификата нет ошибок.
   - Перезапустите бота (`python main.py`) и попробуйте снова.

### 4. Получение ID администраторов

### 3. Получение ID администраторов

1. Найдите вашего бота в Telegram: [@userinfobot](https://t.me/userinfobot)
2. Отправьте ему команду `/start`
3. Скопируйте ваш `Id`
4. Добавьте в `.env`: `ADMIN_CHAT_IDS=ваш_id`

Или для группового чата:
1. Добавьте бота в группу
2. Отправьте команду `/start`
3. Найдите ID группы через API: `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. ID группы начинается с `-` (например, `-1234567890`)

### 4. Обновление конфигурации Frontend

Откройте `frontend/src/config/app.config.ts` и обновите:

```typescript
export const TELEGRAM_CONFIG = {
  botToken: 'ваш_токен',  // Не обязательно для frontend
  adminIds: [ваш_telegram_id, другой_id] as number[],
  supportUsername: 'support_username',  // Username саппорта
};
```

---

## 📡 API документация

### Публичные эндпоинты

| Метод | Путь | Описание | Ответ |
|-------|------|----------|-------|
| `GET` | `/api/health` | Health check | `{"status": "healthy"}` |
| `GET` | `/api/brands` | Получить все бренды | `Brand[]` |
| `GET` | `/api/categories` | Получить все категории | `Category[]` |
| `GET` | `/api/categories/{brand_id}` | Категории бренда | `Category[]` |
| `GET` | `/api/brands/{category_id}` | Бренды категории | `Brand[]` |
| `GET` | `/api/products` | Получить все товары | `Product[]` |
| `GET` | `/api/products/{category_id}` | Товары категории | `Product[]` |

### Заказы

| Метод | Путь | Описание | Тело запроса |
|-------|------|----------|--------------|
| `POST` | `/api/orders/create` | Создать заказ | `OrderCreate` |
| `GET` | `/api/orders/{order_id}` | Детали заказа | - |
| `GET` | `/api/orders/{order_id}/status` | Статус заказа | - |
| `GET` | `/api/orders/user/{user_id}` | История заказов пользователя | - |

### Платежи

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/payment/details` | Получить данные для оплаты |
| `POST` | `/api/payment/confirm` | Подтвердить оплату |
| `POST` | `/api/payment/cancel` | Отменить заказ |

### Админ эндпоинты

| Метод | Путь | Описание | Тело запроса |
|-------|------|----------|--------------|
| `GET` | `/api/admin/data` | Данные для админ-панели | - |
| `POST` | `/api/admin/add_product` | Добавить товар | `FormData` |
| `POST` | `/api/admin/add_brand` | Добавить бренд | `name: string` |
| `POST` | `/api/admin/add_category` | Добавить категорию | `name: string` |
| `POST` | `/api/admin/edit_product` | Редактировать товар | `FormData` |
| `POST` | `/api/admin/delete_product` | Удалить товар | `product_id: int` |

### Статистика пользователя

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/user/{user_id}/stats` | Статистика пользователя |

### Модели данных

#### Brand
```typescript
{
  id: number;
  name: string;
  image_url?: string;
}
```

#### Category
```typescript
{
  id: number;
  name: string;
  brand_id?: number;
}
```

#### Product
```typescript
{
  id: number;
  name: string;
  price: number;
  photo_url?: string;
  description?: string;
  category_id: number;
  brand_id?: number;
}
```

#### OrderCreate
```typescript
{
  user_id: number;
  user_name: string;
  username?: string;
  phone: string;
  address: string;
  comment?: string;
  items: Array<{
    product_id: number;
    product_name: string;
    quantity: number;
    price: number;
  }>;
  total: number;
}
```

---

## 🗄️ Структура базы данных

### Таблица: `brands`

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| `name` | VARCHAR(100) | Название бренда (уникальное) |

### Таблица: `categories`

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| `name` | VARCHAR(100) | Название категории |
| `brand_id` | INTEGER | FOREIGN KEY → brands.id |

### Таблица: `products`

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| `name` | VARCHAR(255) | Название товара |
| `price` | FLOAT | Цена товара |
| `photo_url` | VARCHAR(500) | Путь к изображению |
| `description` | TEXT | Описание товара |
| `category_id` | INTEGER | FOREIGN KEY → categories.id |
| `brand_id` | INTEGER | FOREIGN KEY → brands.id |
| `created_at` | DATETIME | Дата создания |
| `updated_at` | DATETIME | Дата обновления |

### Таблица: `orders`

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| `order_id` | VARCHAR(50) | Уникальный ID заказа (ORD-ДДММ-ХХ) |
| `user_id` | INTEGER | ID пользователя Telegram |
| `user_name` | VARCHAR(255) | Имя пользователя |
| `username` | VARCHAR(100) | Username пользователя |
| `phone` | VARCHAR(20) | Телефон |
| `address` | TEXT | Адрес доставки |
| `comment` | TEXT | Комментарий к заказу |
| `total` | FLOAT | Общая сумма заказа |
| `status` | VARCHAR(20) | Статус: PENDING, CONFIRMED, REJECTED |
| `created_at` | DATETIME | Дата создания |
| `updated_at` | DATETIME | Дата обновления |

### Таблица: `order_items`

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| `order_id` | INTEGER | FOREIGN KEY → orders.id |
| `product_id` | INTEGER | ID товара |
| `product_name` | VARCHAR(255) | Название товара (на момент заказа) |
| `quantity` | INTEGER | Количество |
| `price` | FLOAT | Цена за единицу (на момент заказа) |

### Таблица: `order_action_logs`

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| `order_id` | INTEGER | FOREIGN KEY → orders.id |
| `action` | VARCHAR(50) | Действие (CREATED, CONFIRMED, etc.) |
| `admin_id` | INTEGER | ID администратора |
| `created_at` | DATETIME | Дата действия |

---

## 🧪 Тестирование

### Тестирование API

#### Health Check
```bash
curl http://localhost:8000/api/health
```

#### Получить все бренды
```bash
curl http://localhost:8000/api/brands
```

#### Создать заказ
```bash
curl -X POST http://localhost:8000/api/orders/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123456789,
    "user_name": "Test User",
    "phone": "+79991234567",
    "address": "Test Address",
    "items": [
      {
        "product_id": 1,
        "product_name": "Test Product",
        "quantity": 2,
        "price": 1000.0
      }
    ],
    "total": 2000.0
  }'
```

### Тестирование Telegram бота

1. Запустите бота: `python backend/main.py`
2. Найдите вашего бота в Telegram
3. Отправьте команду `/start`
4. Проверьте работу админ-панели: `/admin`
5. Протестируйте создание заказа через WebApp

### Тестирование Frontend

```bash
# Запуск dev-сервера
cd frontend
npm run dev

# Линтинг
npm run lint

# Сборка для production
npm run build
npm run preview
```

---

## 🚀 Деплой на сервер

### Backend

#### 1. Подготовка сервера

```bash
# Установите Python 3.11+
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Установите зависимости
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Настройка systemd сервиса

Создайте файл `/etc/systemd/system/rshop-api.service`:

```ini
[Unit]
Description=RShop API Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/rshop/backend
Environment="PATH=/var/www/rshop/backend/venv/bin"
ExecStart=/var/www/rshop/backend/venv/bin/python run_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Создайте файл `/etc/systemd/system/rshop-bot.service`:

```ini
[Unit]
Description=RShop Telegram Bot
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/rshop/backend
Environment="PATH=/var/www/rshop/backend/venv/bin"
ExecStart=/var/www/rshop/backend/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 3. Запуск сервисов

```bash
sudo systemctl daemon-reload
sudo systemctl enable rshop-api rshop-bot
sudo systemctl start rshop-api rshop-bot

# Проверка статуса
sudo systemctl status rshop-api
sudo systemctl status rshop-bot
```

#### 4. Настройка Nginx (опционально)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static files
    location /static {
        alias /var/www/rshop/backend/static;
    }

    # Frontend
    location / {
        root /var/www/rshop/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

### Frontend

#### 1. Сборка проекта

```bash
cd frontend
npm run build
```

#### 2. Развертывание

```bash
# Скопируйте содержимое dist/ на сервер
scp -r dist/* user@server:/var/www/rshop/frontend/dist/

# Или используйте CI/CD (GitHub Actions, GitLab CI, etc.)
```

#### 3. Настройка переменных окружения

Обновите `frontend/src/config/app.config.ts` для production:

```typescript
APP_MODE = 'production';
API_BASE_URL = 'https://yourdomain.com';
```

---

## 💻 Разработка и улучшения

### Структура проекта

#### Backend модули

- **`admin/`** - Модульная админ-панель для Telegram бота
  - `brands.py` - управление брендами
  - `categories.py` - управление категориями
  - `products.py` - управление товарами
  - `states.py` - FSM состояния для диалогов
  - `utils.py` - утилиты

- **`api_server.py`** - FastAPI приложение с REST API
- **`main.py`** - Telegram бот (aiogram)
- **`order_handlers.py`** - обработка заказов через бота
- **`telegram_notifications.py`** - уведомления администраторам

#### Frontend структура

- **`pages/`** - основные страницы приложения
- **`components/shop/`** - компоненты магазина
- **`components/admin/`** - компоненты админ-панели
- **`hooks/`** - переиспользуемые React хуки
- **`lib/`** - утилиты и API клиент

### Добавление новых функций

#### 1. Добавление нового API эндпоинта

```python
# backend/api_server.py
@app.post("/api/new-endpoint")
async def new_endpoint(data: YourModel):
    # Ваш код
    return {"success": True}
```

#### 2. Добавление нового компонента

```typescript
// frontend/src/components/shop/NewComponent.tsx
export const NewComponent = () => {
  return <div>New Component</div>;
};
```

#### 3. Добавление новой модели в БД

```python
# backend/models.py
class NewModel(Base):
    __tablename__ = "new_model"
    id = Column(Integer, primary_key=True)
    # ... поля
```

Затем обновите миграции:
```bash
python backend/init_db.py  # Пересоздаст БД
```

### Логирование

Приложение использует структурированное логирование:

- **Backend**: логи в `backend/logs/`
- **Frontend**: логи в консоль браузера и localStorage (dev режим)

Настройка логирования в `backend/logging_config.py`.

---

## 🔧 Troubleshooting

### Проблемы с запуском Backend

#### Ошибка: "Module not found"
```bash
# Убедитесь, что виртуальное окружение активировано
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate      # Windows

# Переустановите зависимости
pip install -r requirements.txt
```

#### Ошибка: "BOT_TOKEN not found"
```bash
# Создайте .env файл в backend/
echo "BOT_TOKEN=ваш_токен" > backend/.env
```

#### Ошибка: "Port 8000 already in use"
```bash
# Измените порт в run_server.py
# Или остановите процесс на порту 8000
lsof -ti:8000 | xargs kill  # Linux/Mac
```

### Проблемы с Frontend

#### Ошибка: "Cannot find module"
```bash
# Удалите node_modules и переустановите
rm -rf node_modules package-lock.json
npm install
```

#### Ошибка: "CORS error"
```bash
# Убедитесь, что API сервер запущен
# Проверьте настройки CORS в api_server.py
```

#### Ошибка: "Telegram WebApp not available"
```bash
# Переключите режим на debug-user или debug-admin
# В frontend/src/config/app.config.ts
APP_MODE = 'debug-user';
```

### Проблемы с базой данных

#### Ошибка: "Database is locked"
```bash
# Убедитесь, что нет других процессов, использующих БД
# Перезапустите приложение
```

#### Ошибка: "Table already exists"
```bash
# Удалите старую БД и пересоздайте
rm backend/data/shop.db
python backend/init_db.py
```

### Проблемы с Telegram ботом

#### Бот не отвечает
1. Проверьте токен в `.env`
2. Убедитесь, что бот запущен: `python backend/main.py`
3. Проверьте логи в `backend/logs/telegram_bot_*.log`

#### WebApp не открывается
1. Проверьте настройки WebApp в BotFather
2. Убедитесь, что URL правильный и доступен
3. Проверьте HTTPS (Telegram требует HTTPS для WebApp)

---

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи в `backend/logs/`
2. Проверьте консоль браузера (F12)
3. Убедитесь, что все сервисы запущены
4. Проверьте конфигурацию в `.env` и `app.config.ts`

---

## 📝 Лицензия

[Укажите лицензию вашего проекта]

---

## 👥 Авторы

[Укажите авторов проекта]

---

**Удачной разработки! 🚀**
