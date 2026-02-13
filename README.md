# Large Scale Microservices Project

پروژه مقیاس‌پذیر مبتنی بر معماری میکروسرویس.

## شروع سریع

### پیش‌نیازها

- [Docker](https://docs.docker.com/get-docker/) و [Docker Compose](https://docs.docker.com/compose/install/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/) (برای Kubernetes)
- [Minikube](https://minikube.sigs.k8s.io/docs/start/) (برای Kubernetes محلی)

---

## اجرا با Docker Compose

```bash
# کلون پروژه
git clone https://github.com/ShadowCoderDev/lagescale_final.git

cd lagescale_final

# اجرای تمام سرویس‌ها
docker-compose up -d

# مشاهده لاگ‌ها
docker-compose logs -f

# توقف سرویس‌ها
docker-compose down

# توقف و حذف volume‌ها
docker-compose down -v
```

### آدرس‌های دسترسی (Docker Compose)

| سرویس | آدرس |
|---|---|
| Frontend | http://localhost:3000 |
| User Service API | http://localhost:8001 |
| Product Service API | http://localhost:8002 |
| Order Service API | http://localhost:8003 |
| Payment Service API | http://localhost:8004 |
| Notification Service API | http://localhost:8005 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |
| RabbitMQ Management | http://localhost:15672 |
| MailHog (ایمیل‌ها) | http://localhost:8025 |

---

## مستندات API (Swagger)

هر سرویس دارای مستندات اتوماتیک Swagger UI و ReDoc است:

| سرویس | Swagger UI | ReDoc | OpenAPI JSON |
|---|---|---|---|
| User Service | http://localhost:8001/docs | http://localhost:8001/redoc | http://localhost:8001/openapi.json |
| Product Service | http://localhost:8002/docs | http://localhost:8002/redoc | http://localhost:8002/openapi.json |
| Order Service | http://localhost:8003/docs | http://localhost:8003/redoc | http://localhost:8003/openapi.json |
| Payment Service | http://localhost:8004/api/docs | http://localhost:8004/api/redoc | http://localhost:8004/api/openapi.json |
| Notification Service | http://localhost:8005/api/docs | http://localhost:8005/api/redoc | http://localhost:8005/api/openapi.json |

---

## اجرا با Kubernetes

### پیش‌نیاز

```bash
# شروع Minikube
minikube start --memory=4096 --cpus=4

# فعال‌سازی Ingress
minikube addons enable ingress
```

### دستورات deploy.sh

```bash
cd lagescale_final/k8s

# دیپلوی کامل (بدون build مجدد)
./deploy.sh

# build ایمیج‌ها و سپس دیپلوی
./deploy.sh --build

# rebuild اجباری تمام ایمیج‌ها و دیپلوی
./deploy.sh --force-build

# مشاهده وضعیت
./deploy.sh --status

# حذف تمام منابع
./deploy.sh --delete

# انتخاب پروفایل Minikube
./deploy.sh --profile my-cluster --build
```

### مراحل دیپلوی اتوماتیک

اسکریپت `deploy.sh` مراحل زیر را به صورت ترتیبی اجرا می‌کند:

1. ایجاد Namespace (`ecommerce`)
2. ایجاد Secrets (رمزهای دیتابیس و JWT)
3. ایجاد ConfigMaps (تنظیمات سرویس‌ها)
4. دیپلوی دیتابیس‌ها (PostgreSQL, MongoDB, RabbitMQ, MailHog)
5. دیپلوی سرویس‌ها (با init container برای Alembic migrations)
6. تنظیم Ingress (Nginx Ingress Controller)
7. دیپلوی Monitoring (Prometheus, Grafana)
8. راه‌اندازی Minikube Tunnel

### آدرس‌های دسترسی (Kubernetes)

| سرویس | آدرس |
|---|---|
| Frontend | http://127.0.0.1 یا http://ecommerce.local |
| API (Users) | http://127.0.0.1/api/users |
| API (Products) | http://127.0.0.1/api/products |
| API (Orders) | http://127.0.0.1/api/orders |
| API (Payments) | http://127.0.0.1/api/payments |
| Grafana | http://127.0.0.1/grafana |
| Prometheus | http://127.0.0.1/prometheus |
| MailHog | http://127.0.0.1/mailhog |

### تنظیم hosts file (اختیاری)

برای استفاده از دامنه‌های محلی، خطوط زیر را به فایل `hosts` اضافه کنید:

**Windows:** `C:\Windows\System32\drivers\etc\hosts`
**Linux/Mac:** `/etc/hosts`

```
127.0.0.1   ecommerce.local
127.0.0.1   api.ecommerce.local
127.0.0.1   grafana.ecommerce.local
127.0.0.1   rabbitmq.ecommerce.local
127.0.0.1   mail.ecommerce.local
```

---

## مانیتورینگ

| سرویس | آدرس (Docker Compose) | آدرس (Kubernetes) | اطلاعات ورود |
|---|---|---|---|
| Prometheus | http://localhost:9090 | http://127.0.0.1/prometheus | - |
| Grafana | http://localhost:3001 | http://127.0.0.1/grafana | `admin` / `admin123` |
| RabbitMQ Management | http://localhost:15672 | http://rabbitmq.ecommerce.local | `guest` / `guest` |
| MailHog | http://localhost:8025 | http://127.0.0.1/mailhog | - |

### Health Check

```bash
curl http://localhost:8001/health  # User Service
curl http://localhost:8002/health  # Product Service
curl http://localhost:8003/health  # Order Service
curl http://localhost:8004/health  # Payment Service
curl http://localhost:8005/health  # Notification Service
```

---

## متغیرهای محیطی مهم

| متغیر | سرویس | توضیح |
|---|---|---|
| `DATABASE_URL` | همه (به جز Product) | آدرس PostgreSQL |
| `MONGODB_URL` | Product Service | آدرس MongoDB |
| `SECRET_KEY` | همه | کلید JWT (باید در همه سرویس‌ها یکسان باشد) |
| `RABBITMQ_HOST` | Order, Product, Notification | آدرس RabbitMQ |
| `SMTP_HOST` | Notification | آدرس سرور SMTP |
| `SUCCESS_RATE` | Payment | نرخ موفقیت شبیه‌ساز پرداخت |
| `USER_SERVICE_URL` | Order | آدرس سرویس کاربران |
| `PRODUCT_SERVICE_URL` | Order | آدرس سرویس محصولات |
| `PAYMENT_SERVICE_URL` | Order | آدرس سرویس پرداخت |

---

## نکات مهم

- **SECRET_KEY** باید در تمام سرویس‌ها یکسان باشد تا توکن‌های JWT معتبر باشند
- در محیط پروداکشن، حتما مقادیر پیش‌فرض secret‌ها و password‌ها را تغییر دهید
- **MailHog** فقط برای محیط توسعه است؛ در پروداکشن از سرور SMTP واقعی استفاده کنید
- **SUCCESS_RATE** پرداخت قابل تنظیم است (پیش‌فرض ۸۰٪ موفقیت)
