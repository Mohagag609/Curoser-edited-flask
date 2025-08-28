#!/usr/bin/env python3
"""Create database tables directly without migrations."""

from app import app
from acc.extensions import db

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("Database tables created successfully!")