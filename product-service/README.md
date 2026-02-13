# Product Service

سرویس مدیریت محصولات و موجودی انبار پروژه Large Scale Microservices.

## معرفی

Product Service مسئول مدیریت کاتالوگ محصولات، جستجو، و سیستم رزرو موجودی است. این سرویس از MongoDB به عنوان دیتابیس استفاده می‌کند و یک Stock Consumer پس‌زمینه‌ای برای دریافت پیام‌های RabbitMQ دارد.

## تکنولوژی‌ها

| تکنولوژی | نسخه | کاربرد |
|---|---|---|
| Python | 3.11 | زبان اصلی |
| FastAPI | 0.109.0 | فریمورک وب |
| Motor | 3.3.2 | درایور async MongoDB |
| MongoDB | 7.0 | دیتابیس |
| RabbitMQ | 3.12 | صف پیام (Message Queue) |
| pika | 1.3.2 | کلاینت RabbitMQ |
| Prometheus | - | مانیتورینگ متریک‌ها |

## ساختار پروژه

```
product-service/
├── app/
│   ├── main.py                 # نقطه ورود FastAPI + lifespan
│   ├── api/
│   │   └── products.py         # روت‌های API
│   ├── core/
│   │   ├── auth.py             # احراز هویت (admin/optional)
│   │   ├── config.py           # تنظیمات
│   │   └── database.py         # اتصال MongoDB
│   ├── models/                 # مدل‌های داده
│   ├── schemas/
│   │   └── product.py          # Pydantic schemas
│   └── services/
│       ├── product_service.py  # لاجیک بیزینسی
│       └── stock_consumer.py   # مصرف‌کننده RabbitMQ
├── Dockerfile
└── requirements.txt
```

## API Endpoints

### محصولات

| متد | مسیر | توضیح | احراز هویت |
|---|---|---|---|
| `GET` | `/api/products/` | لیست محصولات (صفحه‌بندی) | اختیاری |
| `GET` | `/api/products/search/?q=...` | جستجوی محصولات | اختیاری |
| `POST` | `/api/products/` | ایجاد محصول جدید | فقط ادمین |
| `GET` | `/api/products/{product_id}/` | دریافت یک محصول | - |
| `PUT/PATCH` | `/api/products/{product_id}/` | ویرایش محصول | فقط ادمین |
| `DELETE` | `/api/products/{product_id}/` | حذف محصول | فقط ادمین |

### مدیریت موجودی (Stock)

| متد | مسیر | توضیح | احراز هویت |
|---|---|---|---|
| `GET` | `/api/products/{product_id}/stock/` | بررسی موجودی | - |
| `POST` | `/api/products/stock/reserve/` | رزرو موجودی برای سفارش | داخلی |
| `POST` | `/api/products/stock/release/` | آزادسازی رزرو | داخلی |
| `POST` | `/api/products/stock/confirm/` | تایید نهایی رزرو | داخلی |
| `GET` | `/api/products/stock/reservation/{id}/` | دریافت جزئیات رزرو | داخلی |

### سیستم

| متد | مسیر | توضیح |
|---|---|---|
| `GET` | `/health` | بررسی سلامت سرویس |
| `GET` | `/docs` | مستندات Swagger UI |
| `GET` | `/metrics` | متریک‌های Prometheus |

## متغیرهای محیطی

| متغیر | توضیح | مقدار پیش‌فرض |
|---|---|---|
| `MONGODB_URL` | آدرس اتصال MongoDB | `mongodb://localhost:27017` |
| `MONGODB_DB_NAME` | نام دیتابیس | `products` |
| `SECRET_KEY` | کلید رمزنگاری JWT | `change-me-in-production` |
| `RABBITMQ_HOST` | آدرس RabbitMQ | `localhost` |
| `ALLOWED_ORIGINS` | آدرس‌های مجاز CORS | `*` |

## اجرای محلی

```bash
# نصب وابستگی‌ها
pip install -r requirements.txt

# اجرای سرویس
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

> نیاز به اجرای MongoDB و RabbitMQ قبل از شروع سرویس دارید.

## اجرا با Docker

```bash
docker build -t product-service .
docker run -p 8002:8002 \
  -e MONGODB_URL=mongodb://host.docker.internal:27017 \
  -e MONGODB_DB_NAME=products \
  -e SECRET_KEY=my-secret-key \
  -e RABBITMQ_HOST=host.docker.internal \
  product-service
```

## نمونه درخواست‌ها

### لیست محصولات

```bash
curl http://localhost:8002/api/products/?page=1&page_size=10
```

### جستجوی محصولات

```bash
curl "http://localhost:8002/api/products/search/?q=laptop&page=1&page_size=10"
```

### ایجاد محصول (ادمین)

```bash
curl -X POST http://localhost:8002/api/products/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{
    "name": "لپ تاپ ایسوس",
    "description": "لپ تاپ گیمینگ",
    "price": 25000000,
    "stock": 50,
    "is_active": true
  }'
```

## مصرف‌کننده RabbitMQ (Stock Consumer)

سرویس یک consumer پس‌زمینه‌ای دارد که از RabbitMQ پیام‌های مربوط به تغییرات موجودی را دریافت و پردازش می‌کند. این consumer به صورت یک thread جداگانه (daemon) در زمان startup اجرا می‌شود.

## سیستم رزرو موجودی

فرآیند رزرو موجودی در ۳ مرحله انجام می‌شود:

1. **Reserve** - رزرو موجودی هنگام ایجاد سفارش
2. **Confirm** - تایید نهایی پس از پرداخت موفق
3. **Release** - آزادسازی رزرو در صورت لغو سفارش یا شکست پرداخت

## ارتباط با سایر سرویس‌ها

- **Order Service** محصولات و موجودی را از این سرویس استعلام می‌کند
- **Order Service** رزرو موجودی را از طریق API‌های stock انجام می‌دهد
- **RabbitMQ** برای دریافت پیام‌های تغییرات موجودی استفاده می‌شود
