#Requires -Version 5.1
# Deploy ONLY the new twitter-bot repo. Does not change global git/gh config or other repos.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path", "User")

$repoOwner = "Richbit81"
$repoName = "twitter-bot"
$repoFull = "$repoOwner/$repoName"

function Get-GitHubToken {
    $input = "protocol=https`nhost=github.com`n`n"
    $out = ($input | git credential fill 2>$null | Out-String)
    if ($out -match 'password=(.+)') {
        return $Matches[1].Trim()
    }
    throw "No stored GitHub token found."
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

if (-not (Test-Path ".env")) {
    throw ".env missing."
}

$token = Get-GitHubToken
$env:GH_TOKEN = $token

Write-Host "Checking repo $repoFull ..."
$repoExists = $false
try {
    gh repo view $repoFull 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $repoExists = $true }
} catch {
    $repoExists = $false
}
if (-not $repoExists) {
    Write-Host "Creating new repo: $repoFull"
    gh repo create $repoFull --public --description "Auto-tweet bot for richart.app collections"
} else {
    Write-Host "Repo already exists."
}

$remoteUrl = "https://github.com/$repoFull.git"
$existingRemote = $null
try {
    $existingRemote = git remote get-url origin 2>$null
    if ($LASTEXITCODE -ne 0) { $existingRemote = $null }
} catch {
    $existingRemote = $null
}
if (-not $existingRemote) {
    Write-Host "Adding origin remote (local twitter-bot only)."
    git remote add origin $remoteUrl
} elseif ($existingRemote -ne $remoteUrl) {
    Write-Host "Setting origin to $repoFull (local twitter-bot only)."
    git remote set-url origin $remoteUrl
}

$status = git status --porcelain
if ($status) {
    git add deploy-github.ps1 setup-github.ps1 data/history.json main.py 2>$null
    if (-not (git diff --cached --quiet)) {
        git commit -m "Add deployment scripts and bot updates"
    }
}

Write-Host "Setting secrets for $repoFull only ..."
$envVars = Read-DotEnv ".env"
$secrets = @(
    "OPENAI_API_KEY",
    "X_API_KEY",
    "X_API_SECRET",
    "X_ACCESS_TOKEN",
    "X_ACCESS_TOKEN_SECRET"
)
foreach ($name in $secrets) {
    if (-not $envVars[$name]) { throw "Missing in .env: $name" }
    $envVars[$name] | gh secret set $name -R $repoFull
}
$token | gh secret set BOT_GITHUB_TOKEN -R $repoFull

Write-Host "Pushing to $repoFull ..."
git branch -M main
git push -u origin main

Write-Host "Done: https://github.com/$repoFull"

Remove-Item Env:GH_TOKEN -ErrorAction SilentlyContinue
