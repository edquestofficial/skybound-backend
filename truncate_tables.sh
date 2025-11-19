#!/bin/bash

# Truncate Tables Script for MySQL
# This script truncates projects, leads, and employees tables for a company

# MySQL Configuration
DB_HOST="192.168.1.20"
DB_USER="test"
DB_PASS="test"
DB_NAME="Edquestdb"

# Check if alias name is provided
if [ -z "$1" ]; then
    echo "Error: No alias name provided!"
    echo "Usage: ./truncate_tables.sh [alias_name]"
    echo "Example: ./truncate_tables.sh skybound"
    exit 1
fi

ALIAS_NAME="$1"

echo "Starting truncation of tables for company: $ALIAS_NAME"
echo "================================================"

# Truncate projects table
echo "Truncating ${ALIAS_NAME}_projects..."
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "TRUNCATE TABLE \`${ALIAS_NAME}_projects\`;"
if [ $? -eq 0 ]; then
    echo "✓ ${ALIAS_NAME}_projects truncated successfully"
else
    echo "✗ Failed to truncate ${ALIAS_NAME}_projects"
fi

# Truncate leads table
echo "Truncating ${ALIAS_NAME}_leads..."
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "TRUNCATE TABLE \`${ALIAS_NAME}_leads\`;"
if [ $? -eq 0 ]; then
    echo "✓ ${ALIAS_NAME}_leads truncated successfully"
else
    echo "✗ Failed to truncate ${ALIAS_NAME}_leads"
fi



echo "================================================"
echo "Truncation complete!"
echo ""
echo "Usage: ./truncate_tables.sh [alias_name]"
echo "Example: ./truncate_tables.sh skybound"
