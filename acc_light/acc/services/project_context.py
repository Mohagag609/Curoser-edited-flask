from flask import session, g
from acc.models import Project
from acc.services.project_selection import (
    get_current_project_id as get_selected_project_id,
    set_current_project as set_selected_project,
    get_current_project as get_selected_project
)

SESSION_PROJECT_KEY = 'current_project_id'

def get_current_project_id():
    """Get the ID of the current project from the session."""
    # Use the new selection system
    return get_selected_project_id()

def get_current_project():
    """Get the current project from session"""
    # Use the new selection system
    return get_selected_project()

def set_current_project(project_id):
    """Set the current project in session"""
    # Use the new selection system
    set_selected_project(project_id)
    return True

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