#!/bin/bash
# run_tests.sh - Comprehensive test runner
# Usage: ./run_tests.sh [unit|integration|all|coverage|quick]

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_section() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Setup test environment
setup_test_env() {
    log_info "Setting up test environment..."
    
    # Create test database if needed
    export DJANGO_SETTINGS_MODULE=oroshine_app.settings
    export DEBUG=True
    export CELERY_TASK_ALWAYS_EAGER=True
    
    # Clear cache
    python manage.py shell -c "from django.core.cache import cache; cache.clear()"
    
    log_info "Test environment ready"
}

# Run unit tests
run_unit_tests() {
    log_section "Running Unit Tests"
    
    log_info "Testing Models..."
    python manage.py test oroshine_webapp.tests.test_models --verbosity=2
    
    log_info "Testing Forms..."
    python manage.py test oroshine_webapp.tests.test_forms --verbosity=2
    
    log_info "Testing Views..."
    python manage.py test oroshine_webapp.tests.test_views --verbosity=2
    
    log_info "Testing Tasks..."
    python manage.py test oroshine_webapp.tests.test_tasks --verbosity=2
}

# Run integration tests
run_integration_tests() {
    log_section "Running Integration Tests"
    
    python manage.py test oroshine_webapp.tests.test_integration --verbosity=2
}

# Run all tests
run_all_tests() {
    log_section "Running All Tests"
    
    python manage.py test oroshine_webapp.tests --verbosity=2 --parallel=2
}

# Quick smoke tests
run_quick_tests() {
    log_section "Running Quick Smoke Tests"
    
    # Test critical paths only
    python manage.py test \
        oroshine_webapp.tests.test_views.AuthenticationViewsTest.test_login_valid_credentials \
        oroshine_webapp.tests.test_views.AppointmentViewsTest.test_book_appointment_success \
        oroshine_webapp.tests.test_integration.AppointmentBookingFlowTest.test_complete_booking_flow \
        --verbosity=2
}

# Run coverage analysis
run_coverage() {
    log_section "Running Coverage Analysis"
    
    if ! command -v coverage &> /dev/null; then
        log_error "Coverage.py not installed. Installing..."
        pip install coverage
    fi
    
    # Run tests with coverage
    coverage erase
    coverage run --source='oroshine_webapp' manage.py test oroshine_webapp.tests
    
    # Generate reports
    log_info "Generating coverage report..."
    coverage report -m
    
    # Generate HTML report
    coverage html
    log_info "HTML coverage report generated in htmlcov/index.html"
    
    # Check coverage threshold
    COVERAGE=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')
    THRESHOLD=80
    
    if (( $(echo "$COVERAGE < $THRESHOLD" | bc -l) )); then
        log_warn "Coverage is ${COVERAGE}% (below threshold of ${THRESHOLD}%)"
        exit 1
    else
        log_info "Coverage is ${COVERAGE}% (above threshold)"
    fi
}

# Run linting checks
run_linting() {
    log_section "Running Code Quality Checks"
    
    if command -v flake8 &> /dev/null; then
        log_info "Running flake8..."
        flake8 oroshine_webapp --max-line-length=100 --exclude=migrations || true
    fi
    
    if command -v pylint &> /dev/null; then
        log_info "Running pylint..."
        pylint oroshine_webapp --disable=C,R --ignore=migrations || true
    fi
    
    if command -v black &> /dev/null; then
        log_info "Checking code formatting with black..."
        black --check oroshine_webapp --exclude=migrations || true
    fi
}

# Run security checks
run_security_checks() {
    log_section "Running Security Checks"
    
    log_info "Checking for security issues..."
    python manage.py check --deploy
    
    if command -v bandit &> /dev/null; then
        log_info "Running bandit security scanner..."
        bandit -r oroshine_webapp -x */migrations/* || true
    fi
    
    if command -v safety &> /dev/null; then
        log_info "Checking dependencies for vulnerabilities..."
        safety check || true
    fi
}

# Performance tests
run_performance_tests() {
    log_section "Running Performance Tests"
    
    log_info "Testing database query performance..."
    python manage.py test \
        oroshine_webapp.tests.test_integration.PerformanceTest \
        --verbosity=2
}

# Generate test report
generate_report() {
    log_section "Generating Test Report"
    
    REPORT_FILE="test_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "===================================="
        echo "Test Report - $(date)"
        echo "===================================="
        echo ""
        echo "Environment:"
        python --version
        echo "Django: $(python -c 'import django; print(django.get_version())')"
        echo ""
        echo "Test Results:"
        python manage.py test oroshine_webapp.tests --verbosity=1
    } > $REPORT_FILE
    
    log_info "Test report saved to $REPORT_FILE"
}

# Clean up
cleanup() {
    log_info "Cleaning up..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name ".coverage" -delete 2>/dev/null || true
    rm -rf htmlcov/ 2>/dev/null || true
}

# Main execution
main() {
    setup_test_env
    
    case "${1:-all}" in
        unit)
            run_unit_tests
            ;;
        integration)
            run_integration_tests
            ;;
        all)
            run_all_tests
            ;;
        coverage)
            run_coverage
            ;;
        quick)
            run_quick_tests
            ;;
        lint)
            run_linting
            ;;
        security)
            run_security_checks
            ;;
        performance)
            run_performance_tests
            ;;
        full)
            run_linting
            run_security_checks
            run_all_tests
            run_coverage
            generate_report
            ;;
        clean)
            cleanup
            ;;
        *)
            echo "Usage: $0 {unit|integration|all|coverage|quick|lint|security|performance|full|clean}"
            echo ""
            echo "Test Suites:"
            echo "  unit         - Run unit tests only"
            echo "  integration  - Run integration tests only"
            echo "  all          - Run all tests"
            echo "  coverage     - Run tests with coverage analysis"
            echo "  quick        - Run quick smoke tests"
            echo "  lint         - Run code quality checks"
            echo "  security     - Run security checks"
            echo "  performance  - Run performance tests"
            echo "  full         - Run complete test suite with reports"
            echo "  clean        - Clean up test artifacts"
            exit 1
            ;;
    esac
    
    log_info "Tests completed successfully!"
}

# Run main with error handling
main "$@" || {
    log_error "Tests failed!"
    exit 1
}