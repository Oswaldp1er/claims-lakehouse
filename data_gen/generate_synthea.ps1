# Regenerate the synthetic dataset on Windows (PowerShell).
# Requires Java 17+ and Python 3 with pandas (pip install pandas).
# Output: .\data\claims_lakehouse_data\ and .\data\claims_lakehouse_data.zip (both ignored by git).
param(
  [int]$Patients = 500,
  [int]$Seed = 42,
  [string]$State = "Minnesota",
  [string]$FeedStart = "2024-01"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$work = Join-Path $root "data\synthea"
New-Item -ItemType Directory -Force -Path $work | Out-Null
$jar = Join-Path $work "synthea-with-dependencies.jar"
if (-not (Test-Path $jar)) {
  Invoke-WebRequest -Uri "https://github.com/synthetichealth/synthea/releases/download/master-branch-latest/synthea-with-dependencies.jar" -OutFile $jar
}
Push-Location $work
java -jar $jar -s $Seed -cs $Seed -p $Patients `
  --exporter.baseDirectory ./output `
  --exporter.csv.export true --exporter.fhir.export false `
  --exporter.hospital.fhir.export false --exporter.practitioner.fhir.export false `
  --exporter.years_of_history 5 $State
Pop-Location
$out = Join-Path $root "data\claims_lakehouse_data"
python (Join-Path $PSScriptRoot "split_into_payer_feeds.py") --src (Join-Path $work "output\csv") --out $out --feed-start $FeedStart
Compress-Archive -Path $out -DestinationPath (Join-Path $root "data\claims_lakehouse_data.zip") -Force
Write-Host "Done: data\claims_lakehouse_data.zip"
