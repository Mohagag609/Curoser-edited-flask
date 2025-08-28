from app import app, db
from acc.models import Project
from acc.services.utils import generate_uid
from datetime import datetime

with app.app_context():
    try:
        # Test creating a project directly
        project = Project(
            id=generate_uid('PRJ'),
            name='مشروع تجريبي',
            code='TEST-123',
            budget=1000000,
            start_date=datetime.strptime('2025-01-01', '%Y-%m-%d').date(),
            expected_end_date=None,
            description='وصف تجريبي',
            status='نشط'
        )
        
        db.session.add(project)
        db.session.commit()
        
        print(f"Success! Project created with ID: {project.id}")
        
        # Clean up
        db.session.delete(project)
        db.session.commit()
        print("Test project deleted")
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()