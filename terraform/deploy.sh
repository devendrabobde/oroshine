#!/bin/bash
# deploy.sh - Production deployment script for EC2 t2.micro
# Usage: ./deploy.sh
# [setup|deploy|monitor|test|backup|rollback]  

set -e

PROJECT_NAME="oroshine"
APP_DIR="/home/ubuntu/oroshine"
ENV_FILE="$APP_DIR/.env"
BACKUP_DIR="$APP_DIR/backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as correct user
check_user() {
    if [ "$EUID" -eq 0 ]; then
        log_error "Do not run as root. Use ubuntu user."
        exit 1
    fi
}

# Setup function - initial server configuration
setup() {
    log_info "Setting up production environment on EC2 t2.micro..."
    
    # Update system
    log_info "Updating system packages..."
    sudo apt-get update
    sudo apt-get upgrade -y
    
    # Install dependencies
    log_info "Installing dependencies..."
    sudo apt-get install -y \
        python3-pip \
        python3-venv \
        postgresql-client \
        redis-tools \
        git \
        nginx \
        supervisor \
        htop \
        vim
    
    # Install Docker
    if ! command -v docker &> /dev/null; then
        log_info "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker ubuntu
        rm get-docker.sh
        log_warn "Please logout and login again for Docker permissions to take effect"
    fi
    
    # Install Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_info "Installing Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    
    # Create directories
    log_info "Creating project directories..."
    mkdir -p $APP_DIR
    mkdir -p $BACKUP_DIR
    mkdir -p $APP_DIR/logs
    mkdir -p $APP_DIR/staticfiles
    mkdir -p $APP_DIR/media
    mkdir -p $APP_DIR/monitoring
    
    # Setup monitoring directories
    mkdir -p $APP_DIR/monitoring/grafana/{provisioning,dashboards}
    mkdir -p $APP_DIR/monitoring/grafana/provisioning/{datasources,dashboards}
    
    # Configure firewall
    log_info "Configuring firewall..."
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw --force enable
    
    # Optimize for t2.micro (1GB RAM)
    log_info "Optimizing for t2.micro..."
    
    # Add swap space (2GB)
    if [ ! -f /swapfile ]; then
        log_info "Creating swap space..."
        sudo fallocate -l 2G /swapfile
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    fi
    
    # Tune swappiness
    sudo sysctl vm.swappiness=10
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
    
    log_info "Setup complete! Clone your repository and configure .env file"
}

# Deploy function
deploy() {
    log_info "Deploying application..."
    
    cd $APP_DIR
    
    # Check .env file
    if [ ! -f "$ENV_FILE" ]; then
        log_error ".env file not found! Create it before deploying."
        exit 1
    fi
    
    # Pull latest code
    log_info "Pulling latest code..."
    git pull origin main || log_warn "Git pull failed or not a git repo"
    
    # Build and restart containers
    log_info "Building Docker images (optimized for t2.micro)..."
    
    # Stop containers to free memory
    docker-compose down
    
    # Build with memory limits
    docker-compose build --no-cache --parallel --memory 512m
    
    # Collect static files
    log_info "Collecting static files..."
    docker-compose run --rm web python manage.py collectstatic --noinput
    
    # Run migrations
    log_info "Running database migrations..."
    docker-compose run --rm web python manage.py migrate --noinput
    
    # Start services
    log_info "Starting services..."
    docker-compose up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to start..."
    sleep 10
    
    # Check service status
    check_services
    
    log_info "Deployment complete!"
}

# Start monitoring
start_monitoring() {
    log_info "Starting monitoring stack..."
    
    cd $APP_DIR
    
    # Copy monitoring configs
    if [ ! -f "$APP_DIR/monitoring/prometheus.yml" ]; then
        log_warn "Monitoring configs not found. Creating default configs..."
        # Copy your prometheus.yml, alerts.yml here
    fi
    
    # Start monitoring containers
    docker-compose -f docker-compose.monitoring.yml up -d
    
    log_info "Monitoring started!"
    log_info "Grafana: http://$(curl -s ifconfig.me):3000 (admin/admin)"
    log_info "Prometheus: http://$(curl -s ifconfig.me):9090"
}

# Run tests
run_tests() {
    log_info "Running test suite..."
    
    cd $APP_DIR
    
    # Run tests in container
    docker-compose run --rm web python manage.py test
    
    # Check coverage (optional)
    # docker-compose run --rm web coverage run --source='.' manage.py test
    # docker-compose run --rm web coverage report
    
    log_info "Tests complete!"
}

# Check service health
check_services() {
    log_info "Checking service health..."
    
    # Check Docker containers
    if ! docker-compose ps | grep "Up" > /dev/null; then
        log_error "Some containers are not running!"
        docker-compose ps
        exit 1
    fi
    
    # Check web service
    if curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
        log_info "✓ Web service is healthy"
    else
        log_error "✗ Web service is not responding"
    fi
    
    # Check Celery
    if docker-compose exec -T celery_worker celery -A oroshine_app inspect ping > /dev/null 2>&1; then
        log_info "✓ Celery worker is healthy"
    else
        log_error "✗ Celery worker is not responding"
    fi
    
    # Check database
    if docker-compose exec -T db pg_isready -U postgres > /dev/null 2>&1; then
        log_info "✓ Database is healthy"
    else
        log_error "✗ Database is not responding"
    fi
    
    # Check Redis
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_info "✓ Redis is healthy"
    else
        log_error "✗ Redis is not responding"
    fi
}

# Backup database and media
backup() {
    log_info "Creating backup..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"
    
    # Backup database
    log_info "Backing up database..."
    docker-compose exec -T db pg_dump -U postgres oroshine | gzip > $BACKUP_FILE
    
    # Backup media files
    log_info "Backing up media files..."
    tar -czf "$BACKUP_DIR/media_$TIMESTAMP.tar.gz" -C $APP_DIR media/
    
    # Keep only last 7 backups
    log_info "Cleaning old backups (keeping last 7)..."
    cd $BACKUP_DIR
    ls -t backup_*.sql.gz | tail -n +8 | xargs -r rm
    ls -t media_*.tar.gz | tail -n +8 | xargs -r rm
    
    log_info "Backup complete: $BACKUP_FILE"
}

# Rollback to previous version
rollback() {
    log_info "Rolling back to previous version..."
    
    cd $APP_DIR
    
    # Find latest backup
    LATEST_BACKUP=$(ls -t $BACKUP_DIR/backup_*.sql.gz | head -n 1)
    
    if [ -z "$LATEST_BACKUP" ]; then
        log_error "No backup found!"
        exit 1
    fi
    
    log_warn "This will restore database from: $LATEST_BACKUP"
    read -p "Continue? (y/n) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Stop services
        docker-compose down
        
        # Restore database
        gunzip -c $LATEST_BACKUP | docker-compose exec -T db psql -U postgres oroshine
        
        # Restart services
        docker-compose up -d
        
        log_info "Rollback complete!"
    else
        log_info "Rollback cancelled"
    fi
}

# View logs
view_logs() {
    SERVICE=${1:-web}
    docker-compose logs -f --tail=100 $SERVICE
}

# Resource monitoring
monitor_resources() {
    log_info "Monitoring resources (press Ctrl+C to exit)..."
    
    while true; do
        clear
        echo "=== System Resources ==="
        free -h
        echo ""
        df -h /
        echo ""
        echo "=== Docker Stats ==="
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
        sleep 5
    done
}

# Main script
case "$1" in
    setup)
        check_user
        setup
        ;;
    deploy)
        check_user
        deploy
        ;;
    monitor)
        start_monitoring
        ;;
    test)
        run_tests
        ;;
    backup)
        backup
        ;;
    rollback)
        rollback
        ;;
    logs)
        view_logs $2
        ;;
    status)
        check_services
        ;;
    resources)
        monitor_resources
        ;;
    *)
        echo "Usage: $0 {setup|deploy|monitor|test|backup|rollback|logs|status|resources}"
        echo ""
        echo "Commands:"
        echo "  setup      - Initial server setup"
        echo "  deploy     - Deploy/update application"
        echo "  monitor    - Start monitoring stack"
        echo "  test       - Run test suite"
        echo "  backup     - Create database backup"
        echo "  rollback   - Rollback to previous backup"
        echo "  logs       - View logs (optional: service name)"
        echo "  status     - Check service health"
        echo "  resources  - Monitor system resources"
        exit 1
        ;;
esac