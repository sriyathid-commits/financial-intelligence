$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $projectRoot ".env"
if (Test-Path -LiteralPath $envPath) { throw ".env already exists; it was not modified." }
function New-SecretHex([int]$byteCount) {
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $bytes = New-Object byte[] $byteCount; $generator.GetBytes($bytes); return [BitConverter]::ToString($bytes).Replace("-", "").ToLowerInvariant() }
    finally { $generator.Dispose() }
}
$template = Get-Content -LiteralPath (Join-Path $projectRoot ".env.example") -Raw
$template = $template.Replace("POSTGRES_PASSWORD=", "POSTGRES_PASSWORD=$(New-SecretHex 32)")
$template = $template.Replace("REDIS_PASSWORD=", "REDIS_PASSWORD=$(New-SecretHex 32)")
$template = $template.Replace("API_KEY_ANALYST=", "API_KEY_ANALYST=$(New-SecretHex 48)")
$template = $template.Replace("API_KEY_OPERATOR=", "API_KEY_OPERATOR=$(New-SecretHex 48)")
$template = $template.Replace("SANDBOX_PARTNER_WEBHOOK_SECRET=", "SANDBOX_PARTNER_WEBHOOK_SECRET=$(New-SecretHex 48)")
Set-Content -LiteralPath $envPath -Value $template -Encoding ascii
Write-Output "Created .env with unique random local secrets. Keep it private; .env is git-ignored."
