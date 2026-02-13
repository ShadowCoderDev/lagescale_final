# Payment Service

سرویس پردازش پرداخت پروژه Large Scale Microservices.

## معرفی

Payment Service مسئول پردازش پرداخت‌ها، بازپرداخت (Refund) و پیگیری تراکنش‌ها است. این سرویس یک شبیه‌ساز پرداخت با نرخ موفقیت قابل تنظیم (پیش‌فرض ۸۰٪) را پیاده‌سازی کرده است.

## تکنولوژی‌ها

| تکنولوژی | نسخه | کاربرد |
|---|---|---|
| Python | 3.11 | زبان اصلی |
| FastAPI | 0.109.0 | فریمورک وب |
| SQLAlchemy | 2.0.25 | ORM |
| Alembic | 1.13.1 | مایگریشن دیتابیس |
| PostgreSQL | 15 | دیتابیس |
| Prometheus | - | مانیتورینگ متریک‌ها |

## ساختار پروژه

```
payment-service/
├── app/
│   ├── main.py              # نقطه ورود FastAPI
│   ├── api/
│   │   └── payments.py      # روت‌های API
│   ├── core/
│   │   └── config.py        # تنظیمات
│   ├── db/
│   │   └── base.py          # اتصال دیتابیس
│   ├── models/              # مدل‌های دیتابیس
│   ├── schemas/
│   │   └── payment.py       # Pydantic schemas
│   └── services/
│       └── payment_service.py  # لاجیک پردازش پرداخت
├── alembic/                 # مایگریشن‌های دیتابیس
│   └── versions/
├── Dockerfile
├── requirements.txt
└── alembic.ini
```

## API Endpoints

| متد | مسیر | توضیح | احراز هویت |
|---|---|---|---|
| `POST` | `/api/payments/process/` | پردازش پرداخت | داخلی |
| `POST` | `/api/payments/refund/` | بازپرداخت | داخلی |
| `GET` | `/api/payments/{transaction_id}/` | دریافت اطلاعات تراکنش | - |
| `GET` | `/api/payments/order/{order_id}/` | لیست تراکنش‌های یک سفارش | - |
| `GET` | `/health` | بررسی سلامت سرویس | - |
| `GET` | `/api/docs` | مستندات Swagger UI | - |
| `GET` | `/api/redoc` | مستندات ReDoc | - |
| `GET` | `/metrics` | متریک‌های Prometheus | - |

### وضعیت‌های پرداخت (PaymentStatus)

- `success` - پرداخت موفق
- `failed` - پرداخت ناموفق
- `refunded` - بازپرداخت شده
- `pending` - در انتظار

## متغیرهای محیطی

| متغیر | توضیح | مقدار پیش‌فرض |
|---|---|---|
| `DATABASE_URL` | آدرس اتصال PostgreSQL | `postgresql://postgres:postgres@localhost:5432/paymentsdb` |
| `SECRET_KEY` | کلید رمزنگاری | `change-me-in-production` |
| `SUCCESS_RATE` | نرخ موفقیت شبیه‌سازی پرداخت (0.0 تا 1.0) | `0.8` |
| `HOST` | آدرس هاست | `0.0.0.0` |
| `PORT` | پورت سرویس | `8004` |
| `DEBUG` | حالت دیباگ | `false` |

## اجرای محلی

```bash
# نصب وابستگی‌ها
pip install -r requirements.txt

# اجرای مایگریشن
alembic upgrade head

# اجرای سرویس
uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
```

## اجرا با Docker

```bash
docker build -t payment-service .
docker run -p 8004:8004 \
  -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/paymentsdb \
  -e SECRET_KEY=my-secret-key \
  -e SUCCESS_RATE=0.8 \
  payment-service
```

## نمونه درخواست‌ها

### پردازش پرداخت

```bash
curl -X POST http://localhost:8004/api/payments/process/ \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 1,
    "user_id": 1,
    "amount": 250000.00
  }'
```

### بازپرداخت

```bash
curl -X POST http://localhost:8004/api/payments/refund/ \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "txn_abc123"
  }'
```

### دریافت اطلاعات تراکنش

```bash
curl http://localhost:8004/api/payments/txn_abc123/
```

### لیست تراکنش‌های یک سفارش

```bash
curl http://localhost:8004/api/payments/order/1/
```

## نرخ موفقیت پرداخت

سرویس یک شبیه‌ساز پرداخت است. نرخ موفقیت از طریق متغیر محیطی `SUCCESS_RATE` تنظیم می‌شود:

- `1.0` = همه پرداخت‌ها موفق
- `0.8` = ۸۰٪ موفقیت (پیش‌فرض)
- `0.5` = ۵۰٪ موفقیت
- `0.0` = همه پرداخت‌ها ناموفق

## ارتباط با سایر سرویس‌ها

| سرویس | نوع ارتباط | هدف |
|---|---|---|
| **Order Service** | HTTP (فراخوانی شونده) | دریافت درخواست پرداخت و بازپرداخت |
