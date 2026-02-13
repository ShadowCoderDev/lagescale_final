#!/bin/bash

# Usage:
#   ./deploy.sh              # Full deploy
#   ./deploy.sh --build      # Build images then deploy
#   ./deploy.sh --delete     # Delete all resources

set -e

# Terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# WSL/Windows compatibility
IS_WSL=false
if grep -qEi "(Microsoft|WSL)" /proc/version 2>/dev/null; then
    IS_WSL=true
fi

# Convert WSL paths to Windows format
convert_path() {
    local p="$1"
    if $IS_WSL && [[ "$p" == /mnt/* ]]; then
        # /mnt/c/Users/... → C:/Users/...
        local drive_letter="${p:5:1}"
        echo "${drive_letter^^}:/${p:7}"
    else
        echo "$p"
    fi
}

# kubectl wrapper for WSL path conversion
if $IS_WSL && command -v kubectl.exe &> /dev/null; then
    KUBECTL_CMD="kubectl.exe"
elif command -v kubectl &> /dev/null; then
    KUBECTL_CMD="kubectl"
else
    echo "kubectl not found!"
    exit 1
fi

kubectl() {
    local args=()
    for arg in "$@"; do
        # Convert WSL paths for kubectl.exe
        if $IS_WSL && [[ "$arg" == /mnt/* ]]; then
            arg="$(convert_path "$arg")"
        fi
        args+=("$arg")
    done
    $KUBECTL_CMD "${args[@]}"
}

# Docker/minikube wrappers for WSL
if $IS_WSL; then
    docker() { docker.exe "$@"; }
    minikube() { minikube.exe "$@"; }
fi

NAMESPACE="ecommerce"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE=""

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

# Prerequisites check
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed!"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster!"
        log_info "If using Minikube: minikube start"
        exit 1
    fi
    
    log_success "Prerequisites OK"
}

# Build Docker Images
build_images() {
    log_info "🐳 Building Docker images..."
    
    if command -v minikube &> /dev/null && minikube status -p "$PROFILE" &> /dev/null; then
        log_info "🔧 Minikube detected (profile: $PROFILE) - setting Docker environment..."
        eval $(minikube -p "$PROFILE" docker-env)
    fi
    
    cd "$SCRIPT_DIR/.."
    
    services=("user-service" "product-service" "order-service" "payment-service" "notification-service" "frontend")
    
    for service in "${services[@]}"; do
        if [ -d "$service" ]; then
            if docker image inspect "afsari911/$service:latest" &>/dev/null; then
                log_info "✅ Image afsari911/$service:latest already exists, skipping build..."
            elif docker image inspect "$service:latest" &>/dev/null; then
                log_info "✅ Image $service:latest already exists, skipping build..."
                # Tag with correct name for Kubernetes
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

create_secrets() {
    log_info "🔐 Creating Secrets..."
    
    if [ -f "$SCRIPT_DIR/01-secrets.yaml" ]; then
        kubectl apply -f "$SCRIPT_DIR/01-secrets.yaml"
        log_success "Secrets created from file"
    else
        log_warning "01-secrets.yaml not found!"
        log_info "Creating secrets with default values..."
        
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
        
        log_success "Secrets created with default values"
    fi
}

deploy() {
    log_info "🚀 Starting deployment..."
    
    # Step 1: Namespace
    log_info "Step 1: Creating Namespace..."
    kubectl apply -f "$SCRIPT_DIR/00-namespace.yaml"
    log_success "Namespace created"
    
    # Step 2: Secrets
    log_info "Step 2: Creating Secrets..."
    create_secrets
    
    # Step 3: ConfigMaps
    log_info "Step 3: Creating ConfigMaps..."
    kubectl apply -f "$SCRIPT_DIR/02-configmaps.yaml"
    log_success "ConfigMaps created"
    
    # Step 4: Databases
    log_info "Step 4: Deploying databases..."
    kubectl apply -f "$SCRIPT_DIR/databases/"
    log_success "Databases deployed"
    
    # Wait for databases to be ready
    log_info "⏳ Waiting for databases (up to 2 minutes)..."
    kubectl wait --for=condition=available --timeout=120s deployment/user-db -n $NAMESPACE 2>/dev/null || true
    kubectl wait --for=condition=available --timeout=120s deployment/order-db -n $NAMESPACE 2>/dev/null || true
    kubectl wait --for=condition=available --timeout=120s deployment/payment-db -n $NAMESPACE 2>/dev/null || true
    kubectl wait --for=condition=available --timeout=120s deployment/notification-db -n $NAMESPACE 2>/dev/null || true
    kubectl wait --for=condition=available --timeout=120s deployment/mongodb -n $NAMESPACE 2>/dev/null || true
    kubectl wait --for=condition=available --timeout=120s deployment/rabbitmq -n $NAMESPACE 2>/dev/null || true
    kubectl wait --for=condition=available --timeout=120s deployment/mailhog -n $NAMESPACE 2>/dev/null || true
    log_success "Databases and MailHog are ready"
    
    # Step 5: Services
    log_info "Step 5: Deploying services..."
    kubectl apply -R -f "$SCRIPT_DIR/services/"
    log_success "Services deployed"
    
    # Migrations are handled by Alembic init containers
    log_info "⏳ Step 5.5: Waiting for services and auto-migrations..."
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
    
    log_success "Services and migrations are ready"
    
    # Step 6: Ingress
    log_info "Step 6: Enabling Ingress addon and deploying Ingress..."
    if command -v minikube &> /dev/null; then
        log_info "  ↳ Enabling Nginx Ingress Controller addon..."
        minikube addons enable ingress -p "$PROFILE" 2>/dev/null && log_success "Ingress addon enabled" || log_warning "Ingress addon already enabled or error occurred"
        log_info "⏳ Waiting for Ingress Controller..."
        kubectl wait --for=condition=available --timeout=120s deployment/ingress-nginx-controller -n ingress-nginx 2>/dev/null || true
    fi
    kubectl apply -f "$SCRIPT_DIR/03-ingress.yaml"
    log_success "Ingress deployed"
    
    # Step 7: Monitoring
    log_info "Step 7: Deploying Monitoring..."
    kubectl apply -f "$SCRIPT_DIR/monitoring/" 2>/dev/null || log_warning "Monitoring deployment failed (possibly insufficient resources)"
    
    log_success "🎉 Deployment completed successfully!"

    # Step 8: Minikube Tunnel
    if command -v minikube &> /dev/null; then
        echo ""
        log_info "🌐 Step 8: Starting Minikube Tunnel..."
        log_info "Tunnel is required for Ingress access."
        log_info "Starting minikube tunnel in background..."
        nohup minikube tunnel -p "$PROFILE" > /dev/null 2>&1 &
        log_success "Minikube Tunnel started (PID: $!)"
    fi

    echo ""
    echo "=============================================="
    echo "    Access URLs"
    echo "=============================================="
    echo ""
    echo "  Frontend:        http://127.0.0.1"
    echo "  API (Users):     http://127.0.0.1/api/users"
    echo "  API (Products):  http://127.0.0.1/api/products"
    echo "  API (Orders):    http://127.0.0.1/api/orders"
    echo "  API (Payments):  http://127.0.0.1/api/payments"
    echo "  Grafana:         http://127.0.0.1/grafana"
    echo "  Prometheus:      http://127.0.0.1/prometheus"
    echo "  MailHog:         http://127.0.0.1/mailhog"
    echo ""
    echo "  Or with domain (requires hosts file setup):"
    echo "  Frontend:        http://ecommerce.local"
    echo "  API:             http://api.ecommerce.local"
    echo ""
    log_info "Note: If tunnel closes, restart with: minikube tunnel -p $PROFILE"
}

show_status() {
    log_info "📊 Current status:"
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

delete_all() {
    log_warning "⚠️  Deleting all resources..."
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl delete namespace $NAMESPACE --ignore-not-found
        log_success "All resources deleted"
    else
        log_info "Operation cancelled"
    fi
}

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  (none)           Full deploy (existing images are not re-pulled)"
    echo "  --profile NAME   Specify Minikube profile (default: active context)"
    echo "  --build          Build Docker images (new only) then deploy"
    echo "  --force-build    Force rebuild all Docker images then deploy"
    echo "  --status         Show current status"
    echo "  --delete         Delete all resources"
    echo "  --help           Show this help"
    echo ""
    echo "Examples:"
    echo "  ./deploy.sh                                    # Simple deploy"
    echo "  ./deploy.sh --profile my-second-cluster        # Deploy on second cluster"
    echo "  ./deploy.sh --build                            # Build new images and deploy"
    echo "  ./deploy.sh --force-build                      # Rebuild everything"
    echo "  ./deploy.sh --status                           # Show status"
}

# Main
main() {
    echo "=============================================="
    echo "    E-commerce Microservices Deployment"
    echo "=============================================="
    echo ""

    # Parse arguments for profile
    local args=()
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --profile)
                PROFILE="$2"
                shift 2
                ;;
            *)
                args+=("$1")
                shift
                ;;
        esac
    done

    # Auto-detect profile if not specified
    if [ -z "$PROFILE" ]; then
        PROFILE=$(kubectl config current-context 2>/dev/null || echo "minikube")
    fi
    log_info "Using Minikube profile: $PROFILE"
    
    check_prerequisites
    
    case "${args[0]:-}" in
        --build)
            build_images
            deploy
            show_status
            ;;
        --force-build)
            log_info "🔥 Force rebuilding all images..."
            if command -v minikube &> /dev/null && minikube status -p "$PROFILE" &> /dev/null; then
                log_info "🔧 Minikube detected (profile: $PROFILE) - setting Docker environment..."
                eval $(minikube -p "$PROFILE" docker-env)
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
            log_error "Invalid option: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"

