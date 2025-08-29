#!/bin/bash
echo "=== Committing fixes for Render deployment ==="

# Add all changes
git add -A

# Commit with descriptive message
git commit -m "Fix SQLAlchemy relationship conflicts and seed data errors

- Remove duplicate project_stages relationship from Contractor model
- Fix ProjectStage.contractor relationship definition
- Fix project1_id and project2_id undefined error in seed_data.py
- Ensure proper order of variable definitions"

echo "=== Changes committed successfully ==="
echo "Please push to your GitHub repository to deploy on Render"