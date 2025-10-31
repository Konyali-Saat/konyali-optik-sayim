# Test Runner Script - Konyalı Optik Sayım Sistemi (Windows PowerShell)
# Bu script tüm testleri çalıştırır ve coverage raporu oluşturur

param(
    [string]$TestType = "all"
)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Konyalı Optik Sayım - Test Suite" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if pytest is installed
$pytestInstalled = Get-Command pytest -ErrorAction SilentlyContinue
if (-not $pytestInstalled) {
    Write-Host "❌ pytest bulunamadı!" -ForegroundColor Red
    Write-Host "Kurulum için: pip install -r tests\requirements.txt"
    exit 1
}

# Navigate to project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Split-Path -Parent $scriptPath)

# Install test dependencies
Write-Host "📦 Test bağımlılıkları kontrol ediliyor..." -ForegroundColor Yellow
pip install -q -r tests\requirements.txt

# Run tests based on argument
switch ($TestType) {
    "unit" {
        Write-Host "🧪 Unit testler çalıştırılıyor..." -ForegroundColor Yellow
        pytest tests\unit\ -v --cov=backend --cov-report=html --cov-report=term
    }
    
    "integration" {
        Write-Host "🔗 Integration testler çalıştırılıyor..." -ForegroundColor Yellow
        pytest tests\integration\ -v
    }
    
    "all" {
        Write-Host "🚀 Tüm testler çalıştırılıyor..." -ForegroundColor Yellow
        pytest tests\ -v --cov=backend --cov-report=html --cov-report=term-missing
    }
    
    "quick" {
        Write-Host "⚡ Hızlı testler (unit only, no coverage)..." -ForegroundColor Yellow
        pytest tests\unit\ -v --tb=short
    }
    
    default {
        Write-Host "❌ Geçersiz argüman: $TestType" -ForegroundColor Red
        Write-Host "Kullanım: .\run_tests.ps1 [unit|integration|all|quick]"
        exit 1
    }
}

# Check test results
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Tüm testler başarılı!" -ForegroundColor Green
    Write-Host ""
    
    if ($TestType -ne "quick") {
        Write-Host "📊 Coverage raporu: htmlcov\index.html"
        Write-Host "   Açmak için: start htmlcov\index.html"
    }
    
    exit 0
} else {
    Write-Host ""
    Write-Host "❌ Bazı testler başarısız oldu!" -ForegroundColor Red
    exit 1
}

