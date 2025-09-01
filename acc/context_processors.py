"""Context processors for template variables"""
from flask import session
from acc.services.utils import format_currency
from acc.services.project_selection import get_current_project

def inject_global_vars():
    """Inject commonly used variables into all templates"""
    return {
        'session': session,
        'format_currency': format_currency,
        'current_project': get_current_project(),
        'user_name': session.get('user_name', 'زائر'),
        'user_id': session.get('user_id', None),
        'is_authenticated': 'user_id' in session
    }