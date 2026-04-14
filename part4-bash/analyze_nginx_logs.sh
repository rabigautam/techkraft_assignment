#!/bin/bash

# --------------------------------------
# Nginx Log Analyzer
# --------------------------------------

LOG_FILE="$1"

if [[ -z "$LOG_FILE" ]]; then
  echo "Usage: $0 <nginx_access_log_file>"
  exit 1
fi

if [[ ! -f "$LOG_FILE" ]]; then
  echo "Error: File not found - $LOG_FILE"
  exit 1
fi

echo "======================================"
echo "         Nginx Log Report"
echo "======================================"

TOTAL_REQUESTS=$(wc -l < "$LOG_FILE")

echo ""
echo "Total Requests: $TOTAL_REQUESTS"
echo ""

# --------------------------------------
# Top 10 IPs
# --------------------------------------
echo "Top 10 IP Addresses:"
awk '{print $1}' "$LOG_FILE" \
  | sort \
  | uniq -c \
  | sort -nr \
  | head -10 \
  | awk '{printf "%-5s %s\n", $1, $2}'

echo ""

# --------------------------------------
# Error Analysis (4xx and 5xx)
# --------------------------------------

TOTAL_4XX=$(awk '$9 ~ /^4/ {count++} END {print count+0}' "$LOG_FILE")
TOTAL_5XX=$(awk '$9 ~ /^5/ {count++} END {print count+0}' "$LOG_FILE")

ERROR_4XX_PERCENT=$(awk -v total="$TOTAL_REQUESTS" -v err="$TOTAL_4XX" 'BEGIN {
  if (total > 0) printf "%.2f", (err/total)*100;
  else print 0
}')

ERROR_5XX_PERCENT=$(awk -v total="$TOTAL_REQUESTS" -v err="$TOTAL_5XX" 'BEGIN {
  if (total > 0) printf "%.2f", (err/total)*100;
  else print 0
}')

echo "Error Analysis:"
echo "4xx Errors: $TOTAL_4XX ($ERROR_4XX_PERCENT%)"
echo "5xx Errors: $TOTAL_5XX ($ERROR_5XX_PERCENT%)"

echo ""

# --------------------------------------
# Top 10 Endpoints
# --------------------------------------
echo "Top 10 Endpoints:"

awk '{print $7}' "$LOG_FILE" \
  | grep -v "^$" \
  | sort \
  | uniq -c \
  | sort -nr \
  | head -10 \
  | awk '{printf "%-5s %s\n", $1, $2}'

echo ""

echo "======================================"
echo "Report Completed"
echo "======================================"