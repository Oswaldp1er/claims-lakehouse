#!/usr/bin/env bash
# Regenerate the synthetic dataset on macOS/Linux.
# Requires Java 17+ and Python 3 with pandas (pip install pandas).
# Usage: ./data_gen/generate_synthea.sh [patients] [seed] [state] [feed_start]
set -euo pipefail
PATIENTS="${1:-500}"; SEED="${2:-42}"; STATE="${3:-Minnesota}"; FEED_START="${4:-2024-01}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$ROOT/data/synthea"; mkdir -p "$WORK"
JAR="$WORK/synthea-with-dependencies.jar"
[ -f "$JAR" ] || curl -sSL -o "$JAR" https://github.com/synthetichealth/synthea/releases/download/master-branch-latest/synthea-with-dependencies.jar
(cd "$WORK" && java -jar "$JAR" -s "$SEED" -cs "$SEED" -p "$PATIENTS" \
  --exporter.baseDirectory ./output \
  --exporter.csv.export true --exporter.fhir.export false \
  --exporter.hospital.fhir.export false --exporter.practitioner.fhir.export false \
  --exporter.years_of_history 5 "$STATE")
python3 "$ROOT/data_gen/split_into_payer_feeds.py" --src "$WORK/output/csv" --out "$ROOT/data/claims_lakehouse_data" --feed-start "$FEED_START"
(cd "$ROOT/data" && rm -f claims_lakehouse_data.zip && zip -qr claims_lakehouse_data.zip claims_lakehouse_data)
echo "Done: data/claims_lakehouse_data.zip"
