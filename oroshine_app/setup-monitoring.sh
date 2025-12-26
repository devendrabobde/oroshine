#!/bin/bash

# Monitoring Setup Script for Oroshine
# Sets up Prometheus, Grafana, Node Exporter, and cAdvisor

set -e

echo "🚀 Setting up monitoring stack for Oroshine..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create monitoring directories
echo -e "${YELLOW}Creating directory structure...${NC}"
mkdir -p monitoring/prometheus
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/provisioning/dashboards
mkdir -p monitoring/grafana/dashboards
mkdir -p nginx/conf.d

# Set proper permissions
echo -e "${YELLOW}Setting permissions...${NC}"
sudo chown -R 472:472 monitoring/grafana 2>/dev/null || true
chmod -R 755 monitoring

# Add Grafana credentials to .env if not exists
if ! grep -q "GRAFANA_USER" .env; then
    echo -e "${YELLOW}Adding Grafana credentials to .env...${NC}"
    echo "" >> .env
    echo "# Grafana Configuration" >> .env
    echo "GRAFANA_USER=admin" >> .env
    echo "GRAFANA_PASSWORD=admin" >> .env
    echo -e "${GREEN}✓ Added Grafana credentials (default: admin/admin)${NC}"
fi

# Pull required images
echo -e "${YELLOW}Pulling Docker images...${NC}"
docker pull prom/prometheus:v2.48.0
docker pull grafana/grafana:10.2.3
docker pull prom/node-exporter:v1.7.0
docker pull gcr.io/cadvisor/cadvisor:v0.47.2

echo -e "${GREEN}✓ Docker images pulled successfully${NC}"

# Stop existing containers if running
echo -e "${YELLOW}Stopping existing monitoring containers...${NC}"
docker-compose -f docker-compose.prod.yml stop prometheus grafana node_exporter cadvisor 2>/dev/null || true

# Start monitoring stack
echo -e "${YELLOW}Starting monitoring stack...${NC}"
docker-compose -f docker-compose.prod.yml up -d prometheus grafana node_exporter cadvisor

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Check if services are running
if docker ps | grep -q "oroshine_prometheus"; then
    echo -e "${GREEN}✓ Prometheus is running${NC}"
else
    echo -e "${YELLOW}⚠ Prometheus failed to start${NC}"
fi

if docker ps | grep -q "oroshine_grafana"; then
    echo -e "${GREEN}✓ Grafana is running${NC}"
else
    echo -e "${YELLOW}⚠ Grafana failed to start${NC}"
fi

if docker ps | grep -q "oroshine_node_exporter"; then
    echo -e "${GREEN}✓ Node Exporter is running${NC}"
else
    echo -e "${YELLOW}⚠ Node Exporter failed to start${NC}"
fi

if docker ps | grep -q "oroshine_cadvisor"; then
    echo -e "${GREEN}✓ cAdvisor is running${NC}"
else
    echo -e "${YELLOW}⚠ cAdvisor failed to start${NC}"
fi

# Display access information
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Monitoring Stack Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📊 Access URLs:"
echo "  - Grafana:     http://localhost:3000"
echo "  - Prometheus:  http://localhost:9090"
echo "  - Node Exporter: http://localhost:9100"
echo "  - cAdvisor:    http://localhost:8080"
echo ""
echo "🔐 Default Grafana Credentials:"
echo "  Username: admin"
echo "  Password: admin"
echo "  (You'll be prompted to change on first login)"
echo ""
echo "📈 Dashboard:"
echo "  The Oroshine dashboard should be automatically loaded"
echo ""
echo "💡 Quick Commands:"
echo "  - View logs:    docker-compose -f docker-compose.prod.yml logs -f grafana"
echo "  - Restart:      docker-compose -f docker-compose.prod.yml restart grafana"
echo "  - Stop all:     docker-compose -f docker-compose.prod.yml down"
echo ""
echo -e "${YELLOW}⚠️  Important Notes:${NC}"
echo "  1. Change the default Grafana password immediately"
echo "  2. For production, set up proper authentication"
echo "  3. Consider exposing Grafana via nginx with SSL"
echo "  4. Monitor resource usage on t2.micro (limited resources)"
echo ""