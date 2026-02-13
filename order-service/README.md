# Order Service

سرویس مدیریت سفارشات پروژه Large Scale Microservices.

## معرفی

Order Service مسئول فرآیند checkout، ایجاد سفارش، پیگیری وضعیت و لغو سفارشات است. این سرویس به عنوان Orchestrator عمل می‌کند و با User Service، Product Service و Payment Service ارتباط برقرار کرده و رویدادهای سفارش را از طریق RabbitMQ منتشر می‌کند.

## تکنولوژی‌ها

| تکنولوژی | نسخه | کاربرد |
|---|---|---|
| Python | 3.11 | زبان اصلی |
| FastAPI | 0.109.0 | فریمورک وب |
| SQLAlchemy | 2.0.25 | ORM |
| Alembic | 1.13.1 | مایگریشن دیتابیس |
| PostgreSQL | 15 | دیتابیس |
| pika | 1.3.2 | کلاینت RabbitMQ |
| tenacity | 8.2.3 | مکانیزم Retry |
| Prometheus | - | مانیتورینگ متریک‌ها |

## ساختار پروژه

```
order-service/
├── app/
│   ├── main.py              # نقطه ورود FastAPI
│   ├── api/
│   │   └── orders.py        # روت‌های API
│   ├── core/
│   │   ├── auth.py          # احراز هویت via JWT
│   │   ├── config.py        # تنظیمات
│   │   └── database.py      # اتصال PostgreSQL
│   ├── models/
│   │   └── order.py         # مدل‌های Order و OrderItem
│   ├── schemas/
│   │   └── order.py         # Pydantic schemas
│   └── services/
│       └── order_service.py # لاجیک بیزینسی و ارتباط با سرویس‌ها
├── alembic/                 # مایگریشن‌های دیتابیس
│   └── versions/
├── Dockerfile
├── requirements.txt
└── alembic.ini
```

## API Endpoints

| متد | مسیر | توضیح | احراز هویت |
|---|---|---|---|
| `POST` | `/api/orders/` | ایجاد سفارش (checkout) | نیاز به توکن |
| `GET` | `/api/orders/` | لیست سفارشات کاربر | نیاز به توکن |
| `GET` | `/api/orders/{order_id}` | دریافت جزئیات سفارش | نیاز به توکن |
| `POST` | `/api/orders/{order_id}/cancel` | لغو سفارش | نیاز به توکن |
| `GET` | `/health` | بررسی سلامت سرویس | - |
| `GET` | `/docs` | مستندات Swagger UI | - |
| `GET` | `/metrics` | متریک‌های Prometheus | - |

### پارامترهای لیست سفارشات

| پارامتر | نوع | توضیح | پیش‌فرض |
|---|---|---|---|
| `status` | string | فیلتر بر اساس وضعیت سفارش | - |
| `page` | int | شماره صفحه | `1` |
| `page_size` | int | تعداد آیتم در صفحه (حداکثر ۱۰۰) | `20` |

### وضعیت‌های سفارش (OrderStatus)

- `pending` - در انتظار پردازش
- `processing` - در حال پردازش
- `paid` - پرداخت شده
- `shipped` - ارسال شده
- `delivered` - تحویل داده شده
- `canceled` - لغو شده
- `failed` - ناموفق

## متغیرهای محیطی

| متغیر | توضیح | مقدار پیش‌فرض |
|---|---|---|
| `DATABASE_URL` | آدرس اتصال PostgreSQL | `postgresql://postgres:postgres@localhost:5432/orderdb` |
| `SECRET_KEY` | کلید رمزنگاری JWT | `change-me-in-production` |
| `ALGORITHM` | الگوریتم JWT | `HS256` |
| `USER_SERVICE_URL` | آدرس User Service | `http://localhost:8000` |
| `PRODUCT_SERVICE_URL` | آدرس Product Service | `http://localhost:8002` |
| `PAYMENT_SERVICE_URL` | آدرس Payment Service | `http://localhost:8004` |
| `RABBITMQ_HOST` | آدرس RabbitMQ | `localhost` |
| `ALLOWED_ORIGINS` | آدرس‌های مجاز CORS | `*` |

## اجرای محلی

```bash
# نصب وابستگی‌ها
pip install -r requirements.txt

# اجرای مایگریشن
alembic upgrade head

# اجرای سرویس
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

> سرویس‌های User، Product، Payment و RabbitMQ باید قبل از این سرویس اجرا شوند.

## اجرا با Docker

```bash
docker build -t order-service .
docker run -p 8003:8003 \
  -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/orderdb \
  -e SECRET_KEY=my-secret-key \
  -e USER_SERVICE_URL=http://user-service:8000 \
  -e PRODUCT_SERVICE_URL=http://product-service:8002 \
  -e PAYMENT_SERVICE_URL=http://payment-service:8004 \
  -e RABBITMQ_HOST=host.docker.internal \
  order-service
```

## نمونه درخواست‌ها

### ایجاد سفارش (Checkout)

```bash
curl -X POST http://localhost:8003/api/orders/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "items": [
      {
        "product_id": "product_object_id",
        "quantity": 2
      }
    ]
  }'
```

### لیست سفارشات

```bash
curl "http://localhost:8003/api/orders/?page=1&page_size=10&status=paid" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### لغو سفارش

```bash
curl -X POST http://localhost:8003/api/orders/1/cancel \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## فرآیند Checkout

```
1. دریافت درخواست سفارش از کاربر
2. بررسی اعتبار محصولات از Product Service
3. رزرو موجودی (Stock Reserve) از Product Service
4. ایجاد سفارش در دیتابیس
5. ارسال درخواست پرداخت به Payment Service
6. در صورت پرداخت موفق:
   ├── تایید رزرو موجودی (Stock Confirm)
   └── انتشار رویداد "order_created" به RabbitMQ
7. در صورت شکست پرداخت:
   ├── آزادسازی رزرو موجودی (Stock Release)
   └── بروزرسانی وضعیت سفارش به "failed"
```

## ارتباط با سایر سرویس‌ها

| سرویس | نوع ارتباط | هدف |
|---|---|---|
| **User Service** | HTTP (REST) | تایید هویت کاربر |
| **Product Service** | HTTP (REST) | استعلام محصول، رزرو/آزادسازی موجودی |
| **Payment Service** | HTTP (REST) | پردازش و بازپرداخت |
| **Notification Service** | RabbitMQ (Async) | اطلاع‌رسانی وضعیت سفارش |
