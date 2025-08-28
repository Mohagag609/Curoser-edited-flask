from app import app, db
from acc.models import Project

with app.app_context():
    # Test inserting a project
    project = Project(
        name='Test Project',
        code='TEST-001',
        description='Test project',
        status='نشط',
        is_default=False,
        budget=1000000
    )
    
    try:
        db.session.add(project)
        db.session.commit()
        print(f"Project created successfully with ID: {project.id}")
    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
        
    # Try to query projects
    projects = Project.query.all()
    print(f"Total projects in DB: {len(projects)}")
    for p in projects:
        print(f"- {p.id}: {p.name}")