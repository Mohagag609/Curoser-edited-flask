#!/usr/bin/env python3
"""Simple seed data for testing"""
from acc import create_app
from acc.extensions import db
from acc.models import Project, Settings
from acc.services.utils import generate_uid

def seed_simple():
    """Add minimal data for testing"""
    app = create_app()
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Add settings if not exist
        if Settings.query.count() == 0:
            settings = Settings(
                company_name='نظام إدارة المشاريع'
            )
            db.session.add(settings)
        
        # Add a simple project
        if Project.query.count() == 0:
            project = Project(
                id=generate_uid('PRJ'),
                name='مشروع تجريبي',
                project_type='عقاري',
                status='نشط',
                location='القاهرة'
            )
            db.session.add(project)
        
        db.session.commit()
        print('✅ Simple seed data added successfully!')
        
        # Show projects
        projects = Project.query.all()
        print(f'\nProjects ({len(projects)}):')
        for p in projects:
            print(f'  - {p.name} (ID: {p.id})')

if __name__ == '__main__':
    seed_simple()