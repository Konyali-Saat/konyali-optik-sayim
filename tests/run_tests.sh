#!/bin/bash

# Test Runner Script - Konyalı Optik Sayım Sistemi
# Bu script tüm testleri çalıştırır ve coverage raporu oluşturur

set -e  # Exit on error

echo "========================================="
echo "  Konyalı Optik Sayım - Test Suite"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest bulunamadı!${NC}"
    echo "Kurulum için: pip install -r tests/requirements.txt"
    exit 1
fi

# Navigate to project root
cd "$(dirname "$0")/.."

# Install test dependencies
echo -e "${YELLOW}📦 Test bağımlılıkları kontrol ediliyor...${NC}"
pip install -q -r tests/requirements.txt

# Run tests based on argument
case "${1:-all}" in
    unit)
        echo -e "${YELLOW}🧪 Unit testler çalıştırılıyor...${NC}"
        pytest tests/unit/ -v --cov=backend --cov-report=html --cov-report=term
        ;;
    
    integration)
        echo -e "${YELLOW}🔗 Integration testler çalıştırılıyor...${NC}"
        pytest tests/integration/ -v
        ;;
    
    all)
        echo -e "${YELLOW}🚀 Tüm testler çalıştırılıyor...${NC}"
        pytest tests/ -v --cov=backend --cov-report=html --cov-report=term-missing
        ;;
    
    quick)
        echo -e "${YELLOW}⚡ Hızlı testler (unit only, no coverage)...${NC}"
        pytest tests/unit/ -v --tb=short
        ;;
    
    *)
        echo -e "${RED}❌ Geçersiz argüman: $1${NC}"
        echo "Kullanım: ./run_tests.sh [unit|integration|all|quick]"
        exit 1
        ;;
esac

# Check test results
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Tüm testler başarılı!${NC}"
    echo ""
    
    if [ "${1:-all}" != "quick" ]; then
        echo "📊 Coverage raporu: htmlcov/index.html"
        echo "   Açmak için: open htmlcov/index.html (macOS)"
        echo "              xdg-open htmlcov/index.html (Linux)"
    fi
    
    exit 0
else
    echo ""
    echo -e "${RED}❌ Bazı testler başarısız oldu!${NC}"
    exit 1
fi

