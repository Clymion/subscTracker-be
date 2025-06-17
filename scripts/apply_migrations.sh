#!/bin/bash
# Script to apply database migrations to the SQLite database

# Set the path to the SQLite database file
DB_FILE="instance/app.db"

# Check if the database file exists
if [ ! -f "$DB_FILE" ]; then
    echo "Database file not found at $DB_FILE"
    read -p "Do you want to create a new database? (y/n): " choice
    if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
        touch "$DB_FILE"
        if [ $? -eq 0 ]; then
            echo "New database created successfully."
        else
            echo "Failed to create the database."
        fi
    else
        echo "Exiting without creating a new database."
        exit 1
    fi
fi

# Apply migrations using Alembic (assuming alembic is configured)
echo "Applying migrations to $DB_FILE..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "Migrations applied successfully."
else
    echo "Failed to apply migrations."
  exit 1
fi
