# Quick API Key Setup and Test Script
# Run this in PowerShell to set your API key and test it

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "OpenAI API Key Setup & Test" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if key is already set
if ($env:OPENAI_API_KEY) {
    Write-Host "✅ API Key already set: $($env:OPENAI_API_KEY.Substring(0,20))..." -ForegroundColor Green
    
    $response = Read-Host "`nUse existing key? (Y/n)"
    if ($response -eq "" -or $response -eq "Y" -or $response -eq "y") {
        Write-Host "`nTesting with existing key...`n" -ForegroundColor Yellow
        python test_real_llm.py
        exit
    }
}

# Prompt for API key
Write-Host "Please enter your OpenAI API key:" -ForegroundColor Yellow
Write-Host "(It should start with 'sk-')" -ForegroundColor Gray
$apiKey = Read-Host "API Key"

# Validate format
if (-not $apiKey.StartsWith("sk-")) {
    Write-Host "`n❌ Invalid API key format. Key should start with 'sk-'" -ForegroundColor Red
    exit 1
}

# Set temporarily
$env:OPENAI_API_KEY = $apiKey
Write-Host "`n✅ API Key set for current session" -ForegroundColor Green

# Ask if permanent
$permanent = Read-Host "`nSave permanently for all sessions? (y/N)"
if ($permanent -eq "y" -or $permanent -eq "Y") {
    [System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", $apiKey, "User")
    Write-Host "✅ API Key saved permanently" -ForegroundColor Green
    Write-Host "   (Restart PowerShell to use in new sessions)" -ForegroundColor Gray
}

# Run test
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Running LLM Tests..." -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

python test_real_llm.py

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
