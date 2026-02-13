# User Service

سرویس مدیریت کاربران و احراز هویت پروژه Large Scale Microservices.

## معرفی

User Service مسئول ثبت‌نام، ورود، مدیریت پروفایل و احراز هویت کاربران است. این سرویس از JWT (JSON Web Tokens) برای احراز هویت استفاده می‌کند و توکن‌ها را هم در کوکی‌های HTTP-Only و هم در بدنه پاسخ ارسال می‌کند.

## تکنولوژی‌ها

| تکنولوژی | نسخه | کاربرد |
|---|---|---|
| Python | 3.11 | زبان اصلی |
| FastAPI | 0.109.0 | فریمورک وب |
| SQLAlchemy | 2.0.25 | ORM |
| Alembic | 1.13.1 | مایگریشن دیتابیس |
| PostgreSQL | 15 | دیتابیس |
| python-jose | - | مدیریت JWT |
| passlib + bcrypt | - | هش کردن رمز عبور |
| Prometheus | - | مانیتورینگ متریک‌ها |

## ساختار پروژه

```
user-service/
├── app/
│   ├── main.py              # نقطه ورود FastAPI
│   ├── api/
│   │   └── users.py         # روت‌های API
│   ├── core/
│   │   ├── auth.py          # لاجیک احراز هویت
│   │   ├── config.py        # تنظیمات و متغیرهای محیطی
│   │   ├── cookies.py       # مدیریت JWT cookies
│   │   ├── database.py      # اتصال به دیتابیس
│   │   └── security.py      # هش و توکن
│   ├── models/
│   │   └── user.py          # مدل دیتابیس User
│   ├── repositories/        # لایه دسترسی به داده
│   ├── schemas/
│   │   └── user.py          # Pydantic schemas
│   └── services/
│       └── user_service.py  # لاجیک بیزینسی
├── alembic/                 # مایگریشن‌های دیتابیس
│   └── versions/
├── Dockerfile
├── requirements.txt
└── alembic.ini
```

## API Endpoints

| متد | مسیر | توضیح | احراز هویت |
|---|---|---|---|
| `POST` | `/api/users/register/` | ثبت‌نام کاربر جدید | - |
| `POST` | `/api/users/login/` | ورود کاربر | - |
| `GET` | `/api/users/profile/` | دریافت پروفایل کاربر | نیاز به توکن |
| `PUT/PATCH` | `/api/users/profile/` | ویرایش پروفایل | نیاز به توکن |
| `POST` | `/api/users/token/refresh/` | بازنوسازی Access Token | نیاز به Refresh Cookie |
| `POST` | `/api/users/logout/` | خروج و پاک کردن کوکی‌ها | نیاز به توکن |
| `GET` | `/health` | بررسی سلامت سرویس | - |
| `GET` | `/docs` | مستندات Swagger UI | - |

## متغیرهای محیطی

| متغیر | توضیح | مقدار پیش‌فرض |
|---|---|---|
| `DATABASE_URL` | آدرس اتصال PostgreSQL | `postgresql://postgres:postgres@localhost:5432/userdb` |
| `SECRET_KEY` | کلید رمزنگاری JWT | `your-secret-key-change-this-in-production` |
| `ALGORITHM` | الگوریتم JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | مدت اعتبار Access Token (دقیقه) | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | مدت اعتبار Refresh Token (روز) | `7` |
| `ALLOWED_ORIGINS` | آدرس‌های مجاز CORS | `*` |

## اجرای محلی

```bash
# نصب وابستگی‌ها
pip install -r requirements.txt

# اجرای مایگریشن
alembic upgrade head

# اجرای سرویس
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## اجرا با Docker

```bash
docker build -t user-service .
docker run -p 8001:8000 \
  -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/userdb \
  -e SECRET_KEY=my-secret-key \
  user-service
```

## نمونه درخواست‌ها

### ثبت‌نام

```bash
curl -X POST http://localhost:8001/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "StrongPass123",
    "first_name": "Ali",
    "last_name": "Ahmadi"
  }'
```

### ورود

```bash
curl -X POST http://localhost:8001/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "StrongPass123"
  }'
```

### دریافت پروفایل

```bash
curl http://localhost:8001/api/users/profile/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## مانیتورینگ

سرویس متریک‌های Prometheus را در مسیر `/metrics` ارائه می‌دهد. متریک‌ها شامل:

- تعداد درخواست‌ها (به تفکیک endpoint و status code)
- زمان پاسخ‌دهی درخواست‌ها
- درخواست‌های فعال

## ارتباط با سایر سرویس‌ها

- **Order Service** از User Service برای تایید هویت کاربران استفاده می‌کند
- توکن‌های JWT تولید شده توسط این سرویس در تمام سرویس‌ها معتبر هستند (با استفاده از `SECRET_KEY` مشترک)
