#!/bin/bash

# =============================================================================
# Deploy Script - اسکریپت استقرار کوبرنتیز
# =============================================================================
# این اسکریپت همه منابع Kubernetes را به ترتیب صحیح deploy می‌کند
# 
# استفاده:
#   ./deploy.sh          # Deploy کامل
#   ./deploy.sh --build  # Build images و سپس Deploy
#   ./deploy.sh --delete # حذف همه منابع
# =============================================================================

set -e  # در صورت خطا متوقف شو

# رنگ‌ها برای خروجی زیباتر
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# متغیرها
NAMESPACE="ecommerce"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# توابع کمکی
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# بررسی پیش‌نیازها
check_prerequisites() {
    log_info "بررسی پیش‌نیازها..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl نصب نیست! لطفاً اول kubectl را نصب کنید."
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "امکان اتصال به Kubernetes cluster نیست!"
        log_info "اگر از Minikube استفاده می‌کنید: minikube start"
        exit 1
    fi
    
    log_success "پیش‌نیازها OK"
}

# Build Docker Images
build_images() {
    log_info "🐳 Building Docker images..."
    
    # اگر از Minikube استفاده می‌شود، محیط Docker را تنظیم کنید
    if command -v minikube &> /dev/null && minikube status &> /dev/null; then
        log_info "🔧 Minikube detected - setting Docker environment..."
        eval $(minikube docker-env)
    fi
    
    cd "$SCRIPT_DIR/.."
    
    # لیست سرویس‌ها
    services=("user-service" "product-service" "order-service" "payment-service" "notification-service" "frontend")
    
    for service in "${services[@]}"; do
        if [ -d "$service" ]; then
            # بررسی اینکه image از قبل وجود دارد یا نه
            if docker image inspect "afsari911/$service:latest" &>/dev/null; then
                log_info "✅ Image afsari911/$service:latest already exists, skipping build..."
            elif docker image inspect "$service:latest" &>/dev/null; then
                log_info "✅ Image $service:latest already exists, skipping build..."
                # تگ‌گذاری با نام صحیح برای Kubernetes
                docker tag "$service:latest" "afsari911/$service:latest"
                log_info "  ↳ Tagged as afsari911/$service:latest"
            else
                log_info "Building $service..."
                docker build -t "afsari911/$service:latest" "./$service"
                log_success "$service built successfully"
            fi
        else
            log_warning "Directory $service not found, skipping..."
        fi
    done
    
    cd "$SCRIPT_DIR"
}

# ایجاد Secrets
create_secrets() {
    log_info "🔐 ایجاد Secrets..."
    
    # بررسی وجود فایل secrets
    if [ -f "$SCRIPT_DIR/01-secrets.yaml" ]; then
        kubectl apply -f "$SCRIPT_DIR/01-secrets.yaml"
        log_success "Secrets از فایل ایجاد شد"
    else
        log_warning "فایل 01-secrets.yaml یافت نشد!"
        log_info "در حال ایجاد secrets با مقادیر پیش‌فرض..."
        
        # ایجاد secrets با مقادیر پیش‌فرض
        kubectl create secret generic database-secrets \
            --namespace=$NAMESPACE \
            --from-literal=postgres-password=postgres123 \
            --from-literal=mongodb-password=mongo123 \
            --from-literal=rabbitmq-password=rabbit123 \
            --dry-run=client -o yaml | kubectl apply -f -
        
        kubectl create secret generic app-secrets \
            --namespace=$NAMESPACE \
            --from-literal=jwt-secret-key=your-super-secret-jwt-key-change-this \
            --from-literal=secret-key=your-app-secret-key-change-this \
            --dry-run=client -o yaml | kubectl apply -f -
        
        log_success "Secrets با مقادیر پیش‌فرض ایجاد شد"
    fi
}

# Deploy اصلی
deploy() {
    log_info "🚀 شروع Deploy..."
    
    # Step 1: Namespace
    log_info "Step 1: ایجاد Namespace..."
    kubectl apply -f "$SCRIPT_DIR/00-namespace.yaml"
    log_success "Namespace ایجاد شد"
    
    # Step 2: Secrets
    log_info "Step 2: ایجاد Secrets..."
    create_secrets
    
    # Step 3: ConfigMaps
    log_info "Step 3: ایجاد ConfigMaps..."
    kubectl apply -f "$SCRIPT_DIR/02-configmaps.yaml"
    log_success "ConfigMaps ایجاد شد"
    
    # Step 4: Databases
    log_info "Step 4: Deploy دیتابیس‌ها..."
    kubectl apply -f "$SCRIPT_DIR/databases/"
    log_success "دیتابیس‌ها deploy شدند"
    
    # صبر برای آماده شدن دیتابیس‌ها
    log_info "⏳ صبر برای آماده شدن دیتابیس‌ها (حداکثر 2 دقیقه)..."
    kubectl wait --for=condition=available --timeout=120s deployment/user-db -n $NAMESPACE 2>/dev/null || true
    kubectl wait --for=condition=available --timeout=120s deployment/order-db -n $NAMESPACE 2>/dev/null || true
    kubectl wait --for=condition=available --timeout=120s deployment/payment-db -n $NAMESPACE 2>/dev/null || true
    kubectl wait --for=condition=available --timeout=120s deployment/notification-db -n $NAMESPACE 2>/dev/null || true
    kubectl wait --for=condition=available --timeout=120s deployment/mongodb -n $NAMESPACE 2>/dev/null || true
    kubectl wait --for=condition=available --timeout=120s deployment/rabbitmq -n $NAMESPACE 2>/dev/null || true
    kubectl wait --for=condition=available --timeout=120s deployment/mailhog -n $NAMESPACE 2>/dev/null || true
    log_success "دیتابیس‌ها و MailHog آماده هستند"
    
    # Step 5: Services
    log_info "Step 5: Deploy سرویس‌ها..."
    kubectl apply -R -f "$SCRIPT_DIR/services/"
    log_success "سرویس‌ها deploy شدند"
    
    # Step 5.5: Wait for all services to be ready
    # Migrations are handled automatically by Alembic init containers:
    #   - user-service: Alembic migration init container
    #   - order-service: Alembic migration init container
    #   - payment-service: Alembic migration init container
    #   - notification-service: Alembic migration init container
    #   - product-service: MongoDB (schema-less, no migration needed)
    log_info "⏳ Step 5.5: صبر برای آماده شدن سرویس‌ها و اجرای خودکار migrations..."
    log_info "  ↳ user-service: Alembic migration via init container"
    log_info "  ↳ order-service: Alembic migration via init container"
    log_info "  ↳ payment-service: Alembic migration via init container"
    log_info "  ↳ notification-service: Alembic migration via init container"
    log_info "  ↳ product-service: MongoDB (no migration needed)"
    
    kubectl wait --for=condition=available --timeout=180s deployment/user-service -n $NAMESPACE 2>/dev/null || log_warning "user-service not ready yet"
    kubectl wait --for=condition=available --timeout=180s deployment/order-service -n $NAMESPACE 2>/dev/null || log_warning "order-service not ready yet"
    kubectl wait --for=condition=available --timeout=180s deployment/payment-service -n $NAMESPACE 2>/dev/null || log_warning "payment-service not ready yet"
    kubectl wait --for=condition=available --timeout=180s deployment/notification-service -n $NAMESPACE 2>/dev/null || log_warning "notification-service not ready yet"
    kubectl wait --for=condition=available --timeout=180s deployment/product-service -n $NAMESPACE 2>/dev/null || log_warning "product-service not ready yet"
    kubectl wait --for=condition=available --timeout=120s deployment/frontend -n $NAMESPACE 2>/dev/null || log_warning "frontend not ready yet"
    
    log_success "سرویس‌ها و Migrations آماده هستند"
    
    # Step 6: Ingress
    log_info "Step 6: Deploy Ingress..."
    kubectl apply -f "$SCRIPT_DIR/03-ingress.yaml"
    log_success "Ingress deploy شد"
    
    # Step 7: Monitoring (اختیاری)
    log_info "Step 7: Deploy Monitoring..."
    kubectl apply -f "$SCRIPT_DIR/monitoring/" 2>/dev/null || log_warning "Monitoring deploy نشد (احتمالاً منابع کافی نیست)"
    
    log_success "🎉 Deploy با موفقیت انجام شد!"
}

# نمایش وضعیت
show_status() {
    log_info "📊 وضعیت فعلی:"
    echo ""
    echo "=== Pods ==="
    kubectl get pods -n $NAMESPACE
    echo ""
    echo "=== Services ==="
    kubectl get svc -n $NAMESPACE
    echo ""
    echo "=== Ingress ==="
    kubectl get ingress -n $NAMESPACE 2>/dev/null || echo "No ingress found"
    echo ""
}

# حذف همه منابع
delete_all() {
    log_warning "⚠️  در حال حذف همه منابع..."
    read -p "آیا مطمئن هستید؟ (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl delete namespace $NAMESPACE --ignore-not-found
        log_success "همه منابع حذف شدند"
    else
        log_info "عملیات لغو شد"
    fi
}

# راهنما
show_help() {
    echo "استفاده: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  (بدون آپشن)    Deploy کامل (imageهای موجود دوباره pull نمی‌شوند)"
    echo "  --build        Build Docker images (فقط imageهای جدید) و سپس Deploy"
    echo "  --force-build  Force rebuild همه Docker images و سپس Deploy"
    echo "  --status       نمایش وضعیت فعلی"
    echo "  --delete       حذف همه منابع"
    echo "  --help         نمایش این راهنما"
    echo ""
    echo "مثال‌ها:"
    echo "  ./deploy.sh              # Deploy ساده (بدون pull دوباره imageها)"
    echo "  ./deploy.sh --build      # Build imageهای جدید و Deploy"
    echo "  ./deploy.sh --force-build # Rebuild همه چیز"
    echo "  ./deploy.sh --status     # نمایش وضعیت"
}

# Main
main() {
    echo "=============================================="
    echo "    E-commerce Microservices Deployment"
    echo "=============================================="
    echo ""
    
    check_prerequisites
    
    case "${1:-}" in
        --build)
            build_images
            deploy
            show_status
            ;;
        --force-build)
            log_info "🔥 Force rebuilding all images..."
            # اگر از Minikube استفاده می‌شود، محیط Docker را تنظیم کنید
            if command -v minikube &> /dev/null && minikube status &> /dev/null; then
                log_info "🔧 Minikube detected - setting Docker environment..."
                eval $(minikube docker-env)
            fi
            cd "$SCRIPT_DIR/.."
            services=("user-service" "product-service" "order-service" "payment-service" "notification-service" "frontend")
            for service in "${services[@]}"; do
                if [ -d "$service" ]; then
                    log_info "Force building $service..."
                    docker build --no-cache -t "afsari911/$service:latest" "./$service"
                    log_success "$service rebuilt successfully"
                fi
            done
            cd "$SCRIPT_DIR"
            deploy
            show_status
            ;;
        --status)
            show_status
            ;;
        --delete)
            delete_all
            ;;
        --help)
            show_help
            ;;
        "")
            deploy
            show_status
            ;;
        *)
            log_error "آپشن نامعتبر: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"

