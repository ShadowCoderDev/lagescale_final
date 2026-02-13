# Usage:
#   .\deploy.ps1              # Full deploy
#   .\deploy.ps1 -Build       # Build images then deploy
#   .\deploy.ps1 -ForceBuild  # Force rebuild all images then deploy
#   .\deploy.ps1 -Status      # Show current status
#   .\deploy.ps1 -Delete      # Delete all resources

param(
    [switch]$Build,
    [switch]$ForceBuild,
    [switch]$Status,
    [switch]$Delete,
    [switch]$Help,
    [string]$Profile = ""  # Minikube profile name (e.g. my-second-cluster)
)

$ErrorActionPreference = "Stop"

$NAMESPACE = "ecommerce"
$SCRIPT_DIR = $PSScriptRoot
$SERVICES = @("user-service", "product-service", "order-service", "payment-service", "notification-service", "frontend")

function Log-Info    { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Log-Success { param($msg) Write-Host "[SUCCESS] $msg" -ForegroundColor Green }
function Log-Warning { param($msg) Write-Host "[WARNING] $msg" -ForegroundColor Yellow }
function Log-Error   { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }

# Auto-detect Minikube profile if not specified
if (-not $Profile) {
    $currentContext = kubectl config current-context 2>$null
    if ($currentContext) {
        $Profile = $currentContext
    } else {
        $Profile = "minikube"
    }
}
Log-Info "Using Minikube profile: $Profile"

function Check-Prerequisites {
    Log-Info "Checking prerequisites..."

    if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
        Log-Error "kubectl is not installed!"
        exit 1
    }

    $null = kubectl cluster-info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Log-Error "Cannot connect to Kubernetes cluster!"
        Log-Info "If using Minikube: minikube start"
        exit 1
    }

    Log-Success "Prerequisites OK"
}

function Build-Images {
    param([switch]$Force)

    Log-Info "🐳 Building Docker images..."

    # Minikube Docker environment
    if (Get-Command minikube -ErrorAction SilentlyContinue) {
        $status = minikube status -p $Profile 2>&1
        if ($LASTEXITCODE -eq 0) {
            Log-Info "🔧 Minikube detected (profile: $Profile) - setting Docker environment..."
            & minikube -p $Profile docker-env --shell powershell | Invoke-Expression
        }
    }

    Push-Location "$SCRIPT_DIR\.."

    foreach ($service in $SERVICES) {
        if (Test-Path $service) {
            if ($Force) {
                Log-Info "Force building $service..."
                docker build --no-cache -t "afsari911/${service}:latest" "./$service"
                Log-Success "$service rebuilt successfully"
            }
            else {
                $inspect = docker image inspect "afsari911/${service}:latest" 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Log-Info "✅ Image afsari911/${service}:latest already exists, skipping..."
                }
                else {
                    Log-Info "Building $service..."
                    docker build -t "afsari911/${service}:latest" "./$service"
                    Log-Success "$service built successfully"
                }
            }
        }
        else {
            Log-Warning "Directory $service not found, skipping..."
        }
    }

    Pop-Location
}

function Create-Secrets {
    Log-Info "🔐 Creating Secrets..."

    $secretsFile = Join-Path $SCRIPT_DIR "01-secrets.yaml"
    if (Test-Path $secretsFile) {
        kubectl apply -f $secretsFile
        Log-Success "Secrets created from file"
    }
    else {
        Log-Warning "01-secrets.yaml not found!"
        Log-Info "Creating secrets with default values..."

        kubectl create secret generic database-secrets `
            --namespace=$NAMESPACE `
            --from-literal=postgres-password=postgres123 `
            --from-literal=mongodb-password=mongo123 `
            --from-literal=rabbitmq-password=rabbit123 `
            --dry-run=client -o yaml | kubectl apply -f -

        kubectl create secret generic app-secrets `
            --namespace=$NAMESPACE `
            --from-literal=jwt-secret-key=your-super-secret-jwt-key-change-this `
            --from-literal=secret-key=your-app-secret-key-change-this `
            --dry-run=client -o yaml | kubectl apply -f -

        Log-Success "Secrets created with default values"
    }
}

function Deploy-All {
    Log-Info "🚀 Starting deployment..."

    # Step 1: Namespace
    Log-Info "Step 1: Creating Namespace..."
    kubectl apply -f "$SCRIPT_DIR\00-namespace.yaml"
    Log-Success "Namespace created"

    # Step 2: Secrets
    Log-Info "Step 2: Creating Secrets..."
    Create-Secrets

    # Step 3: ConfigMaps
    Log-Info "Step 3: Creating ConfigMaps..."
    kubectl apply -f "$SCRIPT_DIR\02-configmaps.yaml"
    Log-Success "ConfigMaps created"

    # Step 4: Databases
    Log-Info "Step 4: Deploying databases..."
    kubectl apply -f "$SCRIPT_DIR\databases\"
    Log-Success "Databases deployed"

    # Wait for databases
    Log-Info "⏳ Waiting for databases (up to 2 minutes)..."
    $dbDeployments = @("user-db", "order-db", "payment-db", "notification-db", "mongodb", "rabbitmq", "mailhog")
    foreach ($db in $dbDeployments) {
        kubectl wait --for=condition=available --timeout=120s "deployment/$db" -n $NAMESPACE 2>$null
        if ($LASTEXITCODE -ne 0) { Log-Warning "$db not ready yet" }
    }
    Log-Success "Databases and MailHog are ready"

    # Step 5: Services
    Log-Info "Step 5: Deploying services..."
    kubectl apply -R -f "$SCRIPT_DIR\services\"
    Log-Success "Services deployed"

    # Step 5.5: Wait for services and migrations
    Log-Info "⏳ Step 5.5: Waiting for services and auto-migrations..."
    Log-Info "  ↳ user-service: Alembic migration via init container"
    Log-Info "  ↳ order-service: Alembic migration via init container"
    Log-Info "  ↳ payment-service: Alembic migration via init container"
    Log-Info "  ↳ notification-service: Alembic migration via init container"
    Log-Info "  ↳ product-service: MongoDB (no migration needed)"

    $svcDeployments = @(
        @{name="user-service"; timeout=180},
        @{name="order-service"; timeout=180},
        @{name="payment-service"; timeout=180},
        @{name="notification-service"; timeout=180},
        @{name="product-service"; timeout=180},
        @{name="frontend"; timeout=120}
    )
    foreach ($svc in $svcDeployments) {
        kubectl wait --for=condition=available --timeout="$($svc.timeout)s" "deployment/$($svc.name)" -n $NAMESPACE 2>$null
        if ($LASTEXITCODE -ne 0) { Log-Warning "$($svc.name) not ready yet" }
    }
    Log-Success "Services and migrations are ready"

    # Step 6: Ingress
    Log-Info "Step 6: Enabling Ingress addon and deploying Ingress..."
    if (Get-Command minikube -ErrorAction SilentlyContinue) {
        Log-Info "↳ Enabling Nginx Ingress Controller addon..."
        minikube addons enable ingress -p $Profile 2>$null
        if ($LASTEXITCODE -eq 0) {
            Log-Success "Ingress addon enabled"
        } else {
            Log-Warning "Ingress addon already enabled or error occurred"
        }
        # Wait for Ingress Controller
        Log-Info "⏳ Waiting for Ingress Controller..."
        kubectl wait --for=condition=available --timeout=120s deployment/ingress-nginx-controller -n ingress-nginx 2>$null
    }
    kubectl apply -f "$SCRIPT_DIR\03-ingress.yaml"
    Log-Success "Ingress deployed"

    # Step 7: Monitoring
    Log-Info "Step 7: Deploying Monitoring..."
    kubectl apply -f "$SCRIPT_DIR\monitoring\" 2>$null
    if ($LASTEXITCODE -ne 0) { Log-Warning "Monitoring deployment failed (possibly insufficient resources)" }

    Log-Success "🎉 Deployment completed successfully!"

    # Step 8: Minikube Tunnel
    if (Get-Command minikube -ErrorAction SilentlyContinue) {
        Write-Host ""
        Log-Info "🌐 Step 8: Starting Minikube Tunnel..."
        Log-Info "Tunnel is required for Ingress access."
        Log-Info "Starting minikube tunnel in a separate window..."
        Start-Process -FilePath "minikube" -ArgumentList "tunnel", "-p", $Profile -WindowStyle Normal
        Log-Success "Minikube Tunnel started (in separate window)"
    }

    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "    Access URLs" -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Frontend:        http://127.0.0.1" -ForegroundColor Green
    Write-Host "  API (Users):     http://127.0.0.1/api/users" -ForegroundColor Green
    Write-Host "  API (Products):  http://127.0.0.1/api/products" -ForegroundColor Green
    Write-Host "  API (Orders):    http://127.0.0.1/api/orders" -ForegroundColor Green
    Write-Host "  API (Payments):  http://127.0.0.1/api/payments" -ForegroundColor Green
    Write-Host "  Grafana:         http://127.0.0.1/grafana" -ForegroundColor Green
    Write-Host "  Prometheus:      http://127.0.0.1/prometheus" -ForegroundColor Green
    Write-Host "  MailHog:         http://127.0.0.1/mailhog" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Or with domain (requires hosts file setup):" -ForegroundColor Yellow
    Write-Host "  Frontend:        http://ecommerce.local" -ForegroundColor Yellow
    Write-Host "  API:             http://api.ecommerce.local" -ForegroundColor Yellow
    Write-Host ""
    Log-Info "Note: If tunnel closes, restart with: minikube tunnel -p $Profile"
}

function Show-Status {
    Log-Info "📊 Current status:"
    Write-Host ""
    Write-Host "=== Pods ==="
    kubectl get pods -n $NAMESPACE
    Write-Host ""
    Write-Host "=== Services ==="
    kubectl get svc -n $NAMESPACE
    Write-Host ""
    Write-Host "=== Ingress ==="
    kubectl get ingress -n $NAMESPACE 2>$null
    if ($LASTEXITCODE -ne 0) { Write-Host "No ingress found" }
    Write-Host ""
}

function Delete-All {
    Log-Warning "⚠️  Deleting all resources..."
    $confirm = Read-Host "Are you sure? (y/N)"
    if ($confirm -eq 'y' -or $confirm -eq 'Y') {
        kubectl delete namespace $NAMESPACE --ignore-not-found
        Log-Success "All resources deleted"
    }
    else {
        Log-Info "Operation cancelled"
    }
}

function Show-Help {
    Write-Host @"
Usage: .\deploy.ps1 [OPTIONS]

Options:
  (none)           Full deploy (images pulled from Docker Hub)
  -Build           Build Docker images (new only) then deploy
  -ForceBuild      Force rebuild all Docker images then deploy
  -Status          Show current status
  -Delete          Delete all resources
  -Help            Show this help

Examples:
  .\deploy.ps1                                    # Simple deploy
  .\deploy.ps1 -Profile my-second-cluster         # Deploy on second cluster
  .\deploy.ps1 -Build                             # Build new images and deploy
  .\deploy.ps1 -ForceBuild                        # Rebuild everything
  .\deploy.ps1 -Status                            # Show status
"@
}

Write-Host ""

Check-Prerequisites

if ($Help) {
    Show-Help
}
elseif ($Status) {
    Show-Status
}
elseif ($Delete) {
    Delete-All
}
elseif ($ForceBuild) {
    Build-Images -Force
    Deploy-All
    Show-Status
}
elseif ($Build) {
    Build-Images
    Deploy-All
    Show-Status
}
else {
    Deploy-All
    Show-Status
}
