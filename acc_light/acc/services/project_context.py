from flask import session, g
from acc.models import Project

SESSION_PROJECT_KEY = 'current_project_id'

def get_current_project_id():
    """Get the ID of the current project from the session."""
    return session.get(SESSION_PROJECT_KEY)

def get_current_project():
    """Get the current project from session"""
    project_id = get_current_project_id()
    
    if not project_id:
        # Try to get default project
        default_project = Project.query.filter_by(is_default=True).first()
        if default_project:
            session['current_project_id'] = default_project.id
            session['current_project_name'] = default_project.name
            session['current_project_code'] = default_project.code
        return default_project
    
    # Get project from cache or database
    if not hasattr(g, 'current_project'):
        g.current_project = Project.query.get(session['current_project_id'])
    
    return g.current_project

def set_current_project(project_id):
    """Set the current project in session"""
    project = Project.query.get(project_id)
    if project:
        session['current_project_id'] = project.id
        session['current_project_name'] = project.name
        session['current_project_code'] = project.code
        session.permanent = True
        return True
    return False

def clear_current_project():
    """Clear the current project from session"""
    session.pop('current_project_id', None)
    session.pop('current_project_name', None)
    session.pop('current_project_code', None)
    if hasattr(g, 'current_project'):
        delattr(g, 'current_project')

def filter_by_project(query, model):
    """Filter query by current project if model has project_id"""
    project = get_current_project()
    if project and hasattr(model, 'project_id'):
        return query.filter_by(project_id=project.id)
    return query