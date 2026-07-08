#Requires -Version 5.1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot ..

$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path", "User")

function Require-GhAuth {
    gh auth status *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "GitHub login required. Complete the browser login..."
        gh auth login -h github.com -p https -w
    }
}

function Read-DotEnv([string]$Path) {
    $vars = @{}
    Get-Content $Path | ForEach-Object {
        if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
        $name, $value = $_ -split '=', 2
        $vars[$name.Trim()] = $value.Trim()
    }
    return $vars
}

Require-GhAuth

if (-not (Test-Path ".env")) {
    throw ".env not found. Copy .env.example to .env and add your keys first."
}

$envVars = Read-DotEnv ".env"
$required = @(
    "OPENAI_API_KEY",
    "X_API_KEY",
    "X_API_SECRET",
    "X_ACCESS_TOKEN",
    "X_ACCESS_TOKEN_SECRET"
)
foreach ($key in $required) {
    if (-not $envVars[$key] -or $envVars[$key] -match '^(your_|sk-\.\.\.)') {
        throw "Missing or placeholder value for $key in .env"
    }
}

$repoName = "twitter-bot"
$user = (gh api user -q .login)
$remote = "https://github.com/$user/$repoName.git"

Write-Host "Creating public repo: $user/$repoName"
gh repo view "$user/$repoName" *> $null
if ($LASTEXITCODE -ne 0) {
    gh repo create $repoName --public --source=. --remote=origin --description "Auto-tweet bot for richart.app collections"
} else {
    git remote remove origin 2>$null
    git remote add origin $remote
}

if (-not (git rev-parse --verify HEAD 2>$null)) {
    git add .
    git commit -m "Initial richart.app twitter bot"
} else {
    $status = git status --porcelain
    if ($status) {
        git add data/history.json main.py
        git commit -m "Update bot history and UTF-8 output fix" 2>$null
        if ($LASTEXITCODE -ne 0) {
            git add .
            git commit -m "Update twitter bot"
        }
    }
}

Write-Host "Setting GitHub Actions secrets..."
$envVars["OPENAI_API_KEY"] | gh secret set OPENAI_API_KEY
$envVars["X_API_KEY"] | gh secret set X_API_KEY
$envVars["X_API_SECRET"] | gh secret set X_API_SECRET
$envVars["X_ACCESS_TOKEN"] | gh secret set X_ACCESS_TOKEN
$envVars["X_ACCESS_TOKEN_SECRET"] | gh secret set X_ACCESS_TOKEN_SECRET

Write-Host "Creating BOT_GITHUB_TOKEN secret..."
$token = gh auth token
$token | gh secret set BOT_GITHUB_TOKEN

Write-Host "Pushing to GitHub..."
git branch -M main
git push -u origin main

Write-Host ""
Write-Host "Done! Repo: https://github.com/$user/$repoName"
Write-Host "Test workflow: https://github.com/$user/$repoName/actions/workflows/tweet.yml"
Write-Host "Click 'Run workflow' once to verify automation."
