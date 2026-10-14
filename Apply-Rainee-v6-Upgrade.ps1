param(
  [string]$Repo = $PSScriptRoot,
  [string]$Bundle = '',
  [string]$Python = 'python',
  [string]$Node = 'node'
)
$ErrorActionPreference = 'Stop'
$UpgradeArguments = @((Join-Path $PSScriptRoot 'apply_rainee_v6_upgrade.py'), '--repo', $Repo, '--node', $Node)
if ($Bundle) { $UpgradeArguments += @('--bundle', $Bundle) }
& $Python @UpgradeArguments
if ($LASTEXITCODE -ne 0) { throw "Upgrade failed with exit code $LASTEXITCODE. See diagnostics above." }
Write-Host 'Reviewed upgrade verified.'
