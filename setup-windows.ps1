<#
    UC007 lab - participant VM setup (Windows).

    Run once in an elevated PowerShell window on your lab VM:

        Set-ExecutionPolicy -Scope Process Bypass -Force
        .\setup-windows.ps1

    Installs Python 3.12, Git, VS Code and the Azure CLI, creates the virtual environment,
    installs the Python packages, and signs you in to Azure.
#>
[CmdletBinding()]
param(
    [switch]$SkipInstalls,
    [string]$VenvPath = "$PSScriptRoot\.venv"
)

$ErrorActionPreference = 'Stop'

function Write-Step($message) { Write-Host "`n=== $message" -ForegroundColor Cyan }
function Test-Command($name) { $null -ne (Get-Command $name -ErrorAction SilentlyContinue) }

if (-not $SkipInstalls) {
    Write-Step 'Installing tools with winget'
    if (-not (Test-Command winget)) {
        throw 'winget not found. Install "App Installer" from the Microsoft Store, then re-run.'
    }
    $packages = @(
        @{ Id = 'Python.Python.3.12';      Check = 'py' },
        @{ Id = 'Git.Git';                 Check = 'git' },
        @{ Id = 'Microsoft.AzureCLI';      Check = 'az' },
        @{ Id = 'Microsoft.VisualStudioCode'; Check = 'code' },
        @{ Id = 'OpenJS.NodeJS.LTS';       Check = 'node' }
    )
    foreach ($package in $packages) {
        if (Test-Command $package.Check) {
            Write-Host "  $($package.Id) already present"
            continue
        }
        Write-Host "  installing $($package.Id) ..."
        winget install --id $package.Id --silent --accept-package-agreements --accept-source-agreements | Out-Null
    }
    # Pick up PATH changes made by the installers
    $env:Path = [System.Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [System.Environment]::GetEnvironmentVariable('Path', 'User')
}

Write-Step 'Creating the Python environment'
$python = if (Test-Command py) { 'py -3.12' } elseif (Test-Command python) { 'python' } else { throw 'Python not found. Open a new PowerShell window and re-run.' }
if (-not (Test-Path $VenvPath)) {
    Invoke-Expression "$python -m venv `"$VenvPath`""
}
$pip = Join-Path $VenvPath 'Scripts\pip.exe'
& $pip install --quiet --upgrade pip
& $pip install --quiet -r (Join-Path $PSScriptRoot 'backend\requirements.txt')
Write-Host '  python packages installed'

Write-Step 'Installing the frontend packages'
Push-Location (Join-Path $PSScriptRoot 'frontend')
npm install --silent
Pop-Location
Write-Host '  npm packages installed'

Write-Step 'Forcing UTF-8 for Python'
# The clinical corpus contains characters (>=, <=) that a cp1252 console cannot print.
[System.Environment]::SetEnvironmentVariable('PYTHONUTF8', '1', 'User')
$env:PYTHONUTF8 = '1'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
# Persist the console encoding so new PowerShell windows render clinical symbols correctly
$profileLine = '[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()'
if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Path $PROFILE -Force | Out-Null }
if (-not (Select-String -Path $PROFILE -SimpleMatch $profileLine -Quiet)) {
    Add-Content -Path $PROFILE -Value $profileLine
}
Write-Host '  PYTHONUTF8=1 and UTF-8 console encoding set'

Write-Step 'Preparing your .env file'
$envFile = Join-Path $PSScriptRoot 'backend\.env'
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $PSScriptRoot 'backend\.env.example') $envFile
    Write-Host "  created $envFile - set LAB_ALIAS to your own short name before continuing"
} else {
    Write-Host "  $envFile already exists"
}

Write-Step 'Signing in to Azure'
if (Test-Command az) {
    az login --use-device-code --only-show-errors | Out-Null
    $subscription = (Get-Content $envFile | Where-Object { $_ -match '^SUBSCRIPTION_ID=' }) -replace '^SUBSCRIPTION_ID=', ''
    if ($subscription -and $subscription -notmatch '^<') {
        az account set --subscription $subscription
    } else {
        Write-Host '  .env still has placeholder values - that is expected on a first run.' -ForegroundColor Yellow
        Write-Host '  After you paste in the handout values, run:  az account set --subscription <SUBSCRIPTION_ID>' -ForegroundColor Yellow
    }
    $who = az ad signed-in-user show --query userPrincipalName -o tsv
    Write-Host "  signed in as $who"
} else {
    Write-Warning 'Azure CLI not on PATH yet. Open a new PowerShell window and run: az login --use-device-code'
}

Write-Step 'Done'
Write-Host @"
Next steps:
  1. Open .env and paste the values from the lab environment handout.
     Set LAB_ALIAS to your own lab username (lowercase letters and digits, e.g. fdeuser7).
  2. Select your subscription:
        az account set --subscription <SUBSCRIPTION_ID from the handout>
        az account show --query "{user:user.name, subscription:name}" -o table
  3. Activate the environment:  .\.venv\Scripts\Activate.ps1
  4. Check it:                  cd backend; python config.py
  5. Follow the lab guide from Part 1.
"@ -ForegroundColor Green
