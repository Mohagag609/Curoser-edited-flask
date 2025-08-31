from flask import jsonify
from acc.api import api
from acc.models import PartnerGroup
from acc.services.project_context import get_current_project

@api.route('/partner-groups')
def get_partner_groups():
    """Get all partner groups"""
    try:
        groups = PartnerGroup.query.all()
        result = []
        for group in groups:
            result.append({
                'id': group.id,
                'code': group.code,
                'name': group.name,
                'total_percentage': float(group.get_total_percentage())
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500