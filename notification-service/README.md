# Notification Service

سرویس اطلاع‌رسانی و ارسال ایمیل پروژه Large Scale Microservices.

## معرفی

Notification Service مسئول ارسال ایمیل‌های اطلاع‌رسانی به کاربران است. این سرویس از RabbitMQ برای دریافت غیرهمزمان رویدادها و از SMTP (MailHog در محیط توسعه) برای ارسال ایمیل استفاده می‌کند.

## تکنولوژی‌ها

| تکنولوژی | نسخه | کاربرد |
|---|---|---|
| Python | 3.11 | زبان اصلی |
| FastAPI | 0.109.0 | فریمورک وب |
| SQLAlchemy | 2.0.25 | ORM |
| Alembic | 1.13.1 | مایگریشن دیتابیس |
| PostgreSQL | 15 | دیتابیس |
| RabbitMQ | 3.12 | صف پیام |
| pika | 1.3.2 | کلاینت RabbitMQ |
| MailHog | - | سرور SMTP تست |
| Prometheus | - | مانیتورینگ متریک‌ها |

## ساختار پروژه

```
notification-service/
├── app/
│   ├── main.py                    # نقطه ورود FastAPI + lifespan
│   ├── api/
│   │   └── notifications.py      # روت‌های API
│   ├── core/
│   │   └── config.py             # تنظیمات
│   ├── models/                   # مدل‌های دیتابیس
│   ├── schemas/                  # Pydantic schemas
│   └── services/
│       ├── email_service.py      # سرویس ارسال ایمیل SMTP
│       └── rabbitmq_consumer.py  # مصرف‌کننده RabbitMQ
├── alembic/                      # مایگریشن‌های دیتابیس
│   └── versions/
├── Dockerfile
├── requirements.txt
└── alembic.ini
```

## API Endpoints

| متد | مسیر | توضیح | احراز هویت |
|---|---|---|---|
| `GET` | `/api/notifications/status/` | وضعیت سرویس (SMTP و RabbitMQ) | - |
| `POST` | `/api/notifications/test/` | ارسال ایمیل تست | - |
| `GET` | `/health` | بررسی سلامت سرویس | - |
| `GET` | `/api/docs` | مستندات Swagger UI | - |
| `GET` | `/api/redoc` | مستندات ReDoc | - |
| `GET` | `/metrics` | متریک‌های Prometheus | - |

### انواع رویدادهای ایمیل (event_type)

| رویداد | توضیح |
|---|---|
| `order_created` | سفارش جدید ایجاد شد |
| `payment_success` | پرداخت موفقیت‌آمیز بود |
| `payment_failed` | پرداخت ناموفق بود |
| `order_canceled` | سفارش لغو شد |

## متغیرهای محیطی

| متغیر | توضیح | مقدار پیش‌فرض |
|---|---|---|
| `DATABASE_URL` | آدرس اتصال PostgreSQL | `postgresql://postgres:postgres@localhost:5432/notificationsdb` |
| `SECRET_KEY` | کلید رمزنگاری | `change-me-in-production` |
| `RABBITMQ_HOST` | آدرس RabbitMQ | `localhost` |
| `RABBITMQ_PORT` | پورت RabbitMQ | `5672` |
| `SMTP_HOST` | آدرس سرور SMTP | `localhost` |
| `SMTP_PORT` | پورت SMTP | `1025` |
| `SMTP_USE_TLS` | استفاده از TLS | `false` |
| `HOST` | آدرس هاست | `0.0.0.0` |
| `PORT` | پورت سرویس | `8005` |

## اجرای محلی

```bash
# نصب وابستگی‌ها
pip install -r requirements.txt

# اجرای مایگریشن
alembic upgrade head

# اجرای سرویس
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

> RabbitMQ و MailHog باید قبل از شروع سرویس اجرا شوند.

## اجرا با Docker

```bash
docker build -t notification-service .
docker run -p 8005:8005 \
  -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/notificationsdb \
  -e SECRET_KEY=my-secret-key \
  -e RABBITMQ_HOST=host.docker.internal \
  -e SMTP_HOST=host.docker.internal \
  -e SMTP_PORT=1025 \
  notification-service
```

## نمونه درخواست‌ها

### بررسی وضعیت سرویس

```bash
curl http://localhost:8005/api/notifications/status/
```

### ارسال ایمیل تست

```bash
curl -X POST http://localhost:8005/api/notifications/test/ \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "user@example.com",
    "event_type": "order_created",
    "order_id": 1,
    "total_amount": 250000.00
  }'
```

### ارسال ایمیل تست پرداخت موفق

```bash
curl -X POST http://localhost:8005/api/notifications/test/ \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "user@example.com",
    "event_type": "payment_success",
    "order_id": 1,
    "transaction_id": "txn_abc123"
  }'
```

## نحوه عملکرد

### مصرف‌کننده RabbitMQ

سرویس یک consumer پس‌زمینه‌ای (daemon thread) دارد که در زمان startup فعال می‌شود:

```
RabbitMQ Queue ──> notification_consumer ──> email_service ──> SMTP (MailHog)
```

1. **Order Service** رویدادی را در RabbitMQ منتشر می‌کند
2. **Notification Consumer** پیام را دریافت می‌کند
3. بر اساس نوع رویداد، ایمیل مناسب ساخته و ارسال می‌شود
4. نتیجه ارسال در دیتابیس ذخیره می‌شود

### مشاهده ایمیل‌ها (MailHog)

در محیط توسعه، ایمیل‌ها به MailHog ارسال می‌شوند و از طریق رابط وب آن قابل مشاهده هستند:

- **MailHog UI**: `http://localhost:8025`

## ارتباط با سایر سرویس‌ها

| سرویس | نوع ارتباط | هدف |
|---|---|---|
| **Order Service** | RabbitMQ (Async) | دریافت رویدادهای سفارش |
| **MailHog** | SMTP | ارسال ایمیل (محیط توسعه) |
