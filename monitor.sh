#!/bin/bash

# OroShine Resource Monitoring Script for t2.micro


GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================================"
echo "🔍 OroShine System Resource Monitor"
echo "================================================"
echo ""

# Memory Usage
echo -e "${GREEN}Memory Usage:${NC}"
free -h
echo ""

# Swap Usage
SWAP_TOTAL=$(free -m | awk 'NR==3 {print $2}')
SWAP_USED=$(free -m | awk 'NR==3 {print $3}')
if [ "$SWAP_TOTAL" -gt 0 ]; then
    SWAP_PERCENT=$(awk "BEGIN {printf \"%.0f\", ($SWAP_USED/$SWAP_TOTAL)*100}")
    if [ "$SWAP_PERCENT" -gt 50 ]; then
        echo -e "${RED}⚠ High Swap Usage: ${SWAP_PERCENT}%${NC}"
    else
        echo -e "${GREEN}✓ Swap Usage: ${SWAP_PERCENT}%${NC}"
    fi
fi
echo ""

# Disk Usage
echo -e "${GREEN}Disk Usage:${NC}"
df -h / | awk 'NR==2 {
    used = substr($5, 1, length($5)-1);
    if (used > 80) 
        printf "\033[0;31m⚠ Disk: %s used (Available: %s)\033[0m\n", $5, $4;
    else if (used > 60)
        printf "\033[1;33m⚠ Disk: %s used (Available: %s)\033[0m\n", $5, $4;
    else
        printf "\033[0;32m✓ Disk: %s used (Available: %s)\033[0m\n", $5, $4;
}'
echo ""

# CPU Load
echo -e "${GREEN}CPU Load Average:${NC}"
uptime | awk -F'load average:' '{print $2}'
echo ""

# Docker Container Status
echo -e "${GREEN}Docker Container Status:${NC}"
cd ~/oroshine_project 2>/dev/null || { echo "Project directory not found"; exit 1; }
docker-compose ps 2>/dev/null || echo "Docker Compose not running"
echo ""

# Container Resource Usage
echo -e "${GREEN}Container Resource Usage:${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || echo "No containers running"
echo ""

# Check for OOM kills
OOM_COUNT=$(dmesg | grep -i "killed process" | wc -l)
if [ "$OOM_COUNT" -gt 0 ]; then
    echo -e "${RED}⚠ WARNING: ${OOM_COUNT} OOM (Out of Memory) kills detected${NC}"
    echo "Recent OOM kills:"
    dmesg | grep -i "killed process" | tail -5
    echo ""
fi

# Docker disk usage
echo -e "${GREEN}Docker Disk Usage:${NC}"
docker system df
echo ""

# Application logs check
echo -e "${GREEN}Recent Application Errors (last 10):${NC}"
docker-compose logs --tail=10 web 2>/dev/null | grep -i "error" || echo "No recent errors"
echo ""

# Recommendations
MEM_PERCENT=$(free | awk 'NR==2 {printf "%.0f", ($3/$2)*100}')
if [ "$MEM_PERCENT" -gt 80 ]; then
    echo -e "${RED}⚠ RECOMMENDATIONS:${NC}"
    echo "  - Memory usage is high (${MEM_PERCENT}%)"
    echo "  - Consider restarting containers: cd ~/oroshine_project && docker-compose restart"
    echo "  - Run cleanup: docker system prune -af"
fi

DISK_PERCENT=$(df / | awk 'NR==2 {print substr($5, 1, length($5)-1)}')
if [ "$DISK_PERCENT" -gt 80 ]; then
    echo -e "${RED}⚠ DISK CLEANUP NEEDED:${NC}"
    echo "  - Run: docker system prune -af --volumes"
    echo "  - Clean logs: sudo journalctl --vacuum-time=2d"
fi

echo ""
echo "================================================"
echo "To monitor in real-time, use:"
echo "  - htop (install: sudo apt install htop)"
echo "  - docker stats"
echo "================================================"