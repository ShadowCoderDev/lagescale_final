# Frontend

رابط کاربری وب پروژه Large Scale Microservices.

## معرفی

Frontend یک اپلیکیشن Single Page Application (SPA) است که با React ساخته شده و در محیط پروداکشن توسط Nginx سرو می‌شود. این اپلیکیشن شامل صفحات ثبت‌نام، ورود، لیست محصولات، سبد خرید و مدیریت سفارشات است.

## تکنولوژی‌ها

| تکنولوژی | نسخه | کاربرد |
|---|---|---|
| React | 18.2.0 | فریمورک UI |
| Vite | 5.0.8 | ابزار Build |
| React Router | 6.20.0 | مسیریابی |
| Axios | 1.6.2 | HTTP Client |
| Nginx | alpine | وب‌سرور (پروداکشن) |
| Node.js | 18 | محیط توسعه |

## ساختار پروژه

```
frontend/
├── src/
│   ├── components/       # کامپوننت‌های قابل استفاده مجدد
│   ├── pages/            # صفحات اپلیکیشن
│   ├── config/           # تنظیمات (API URLs)
│   ├── context/          # React Context (Auth, Cart, ...)
│   ├── utils/            # ابزارهای کمکی
│   ├── App.jsx           # کامپوننت اصلی
│   └── main.jsx          # نقطه ورود
├── public/               # فایل‌های استاتیک
├── nginx.conf            # تنظیمات Nginx پروداکشن
├── Dockerfile            # Multi-stage build (Node → Nginx)
├── package.json
├── vite.config.js
├── .env.example          # متغیرهای محیطی توسعه
└── .env.production       # متغیرهای محیطی پروداکشن
```

## متغیرهای محیطی

### محیط توسعه (.env.example)

| متغیر | توضیح | مقدار |
|---|---|---|
| `VITE_USER_API_BASE_URL` | آدرس User Service | `http://localhost:8000` |
| `VITE_PRODUCT_API_BASE_URL` | آدرس Product Service | `http://localhost:8001` |
| `VITE_ORDER_API_BASE_URL` | آدرس Order Service | `http://localhost:8002` |

### محیط پروداکشن (.env.production)

در پروداکشن، درخواست‌ها از طریق Nginx reverse proxy ارسال می‌شوند و آدرس مستقیم سرویس‌ها لازم نیست.

## اجرای محلی (توسعه)

```bash
# نصب وابستگی‌ها
npm install

# کپی فایل متغیرهای محیطی
cp .env.example .env

# اجرای سرور توسعه
npm run dev
```

سرور توسعه در آدرس `http://localhost:5173` اجرا می‌شود.

## Build پروداکشن

```bash
# ساخت فایل‌های پروداکشن
npm run build

# پیش‌نمایش build
npm run preview
```

## اجرا با Docker

```bash
docker build -t frontend .
docker run -p 3000:80 frontend
```

### Dockerfile (Multi-stage)

فرآیند build در دو مرحله انجام می‌شود:

1. **Stage 1 (Node 18)**: نصب وابستگی‌ها و build اپلیکیشن React
2. **Stage 2 (Nginx)**: کپی فایل‌های build شده و اجرا توسط Nginx

## تنظیمات Nginx

فایل `nginx.conf` شامل:

- سرو فایل‌های استاتیک React
- Reverse proxy برای API‌های بکند
- پشتیبانی از React Router (SPA fallback)

## صفحات اپلیکیشن

| صفحه | مسیر | توضیح |
|---|---|---|
| خانه | `/` | صفحه اصلی |
| ثبت‌نام | `/register` | فرم ثبت‌نام کاربر |
| ورود | `/login` | فرم ورود |
| محصولات | `/products` | لیست محصولات |
| جزئیات محصول | `/products/:id` | جزئیات یک محصول |
| سبد خرید | `/cart` | سبد خرید |
| سفارشات | `/orders` | لیست سفارشات کاربر |

## ارتباط با سایر سرویس‌ها

| سرویس | پورت (Docker Compose) | کاربرد |
|---|---|---|
| **User Service** | 8001 | احراز هویت و پروفایل |
| **Product Service** | 8002 | لیست و جستجوی محصولات |
| **Order Service** | 8003 | ایجاد و پیگیری سفارشات |
