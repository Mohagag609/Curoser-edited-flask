from flask import Blueprint, request, jsonify
from app.services.project_service import ProjectService
from app.services.customer_service import CustomerService
from app.services.unit_service import UnitService
from app.services.contract_service import ContractService
from app.services.installment_service import InstallmentService
from app.services.treasury_service import TreasuryService

api_bp = Blueprint('api', __name__)


@api_bp.route('/projects')
def get_projects():
    """API للحصول على المشاريع"""
    try:
        status = request.args.get('status')
        projects = ProjectService.get_all_projects(status) if status else ProjectService.get_all_projects()
        
        return jsonify({
            'success': True,
            'data': [project.to_dict() for project in projects]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/projects/<project_id>')
def get_project(project_id):
    """API للحصول على مشروع محدد"""
    try:
        project = ProjectService.get_project_by_id(project_id)
        if not project:
            return jsonify({
                'success': False,
                'message': 'المشروع غير موجود'
            }), 404
        
        return jsonify({
            'success': True,
            'data': project.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/customers')
def get_customers():
    """API للحصول على العملاء"""
    try:
        status = request.args.get('status')
        customers = CustomerService.get_all_customers(status) if status else CustomerService.get_all_customers()
        
        return jsonify({
            'success': True,
            'data': [customer.to_dict() for customer in customers]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/customers/<customer_id>')
def get_customer(customer_id):
    """API للحصول على عميل محدد"""
    try:
        customer = CustomerService.get_customer_by_id(customer_id)
        if not customer:
            return jsonify({
                'success': False,
                'message': 'العميل غير موجود'
            }), 404
        
        return jsonify({
            'success': True,
            'data': customer.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/units')
def get_units():
    """API للحصول على الوحدات"""
    try:
        project_id = request.args.get('project_id')
        status = request.args.get('status')
        
        if project_id and status:
            units = UnitService.get_all_units(project_id, status)
        elif project_id:
            units = UnitService.get_all_units(project_id=project_id)
        elif status:
            units = UnitService.get_all_units(status=status)
        else:
            units = UnitService.get_all_units()
        
        return jsonify({
            'success': True,
            'data': [unit.to_dict() for unit in units]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/units/<unit_id>')
def get_unit(unit_id):
    """API للحصول على وحدة محددة"""
    try:
        unit = UnitService.get_unit_by_id(unit_id)
        if not unit:
            return jsonify({
                'success': False,
                'message': 'الوحدة غير موجودة'
            }), 404
        
        return jsonify({
            'success': True,
            'data': unit.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/contracts')
def get_contracts():
    """API للحصول على العقود"""
    try:
        status = request.args.get('status')
        project_id = request.args.get('project_id')
        
        if status and project_id:
            contracts = ContractService.get_all_contracts(status, project_id)
        elif status:
            contracts = ContractService.get_all_contracts(status)
        elif project_id:
            contracts = ContractService.get_all_contracts(project_id=project_id)
        else:
            contracts = ContractService.get_all_contracts()
        
        return jsonify({
            'success': True,
            'data': [contract.to_dict() for contract in contracts]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/contracts/<contract_id>')
def get_contract(contract_id):
    """API للحصول على عقد محدد"""
    try:
        contract = ContractService.get_contract_by_id(contract_id)
        if not contract:
            return jsonify({
                'success': False,
                'message': 'العقد غير موجود'
            }), 404
        
        return jsonify({
            'success': True,
            'data': contract.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/installments')
def get_installments():
    """API للحصول على الأقساط"""
    try:
        status = request.args.get('status')
        contract_id = request.args.get('contract_id')
        
        if status and contract_id:
            installments = InstallmentService.get_all_installments(status, contract_id)
        elif status:
            installments = InstallmentService.get_all_installments(status)
        elif contract_id:
            installments = InstallmentService.get_all_installments(contract_id=contract_id)
        else:
            installments = InstallmentService.get_all_installments()
        
        return jsonify({
            'success': True,
            'data': [installment.to_dict() for installment in installments]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/installments/<installment_id>')
def get_installment(installment_id):
    """API للحصول على قسط محدد"""
    try:
        installment = InstallmentService.get_installment_by_id(installment_id)
        if not installment:
            return jsonify({
                'success': False,
                'message': 'القسط غير موجود'
            }), 404
        
        return jsonify({
            'success': True,
            'data': installment.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/safes')
def get_safes():
    """API للحصول على الخزائن"""
    try:
        project_id = request.args.get('project_id')
        status = request.args.get('status')
        
        if project_id and status:
            safes = TreasuryService.get_all_safes(project_id, status)
        elif project_id:
            safes = TreasuryService.get_all_safes(project_id=project_id)
        elif status:
            safes = TreasuryService.get_all_safes(status=status)
        else:
            safes = TreasuryService.get_all_safes()
        
        return jsonify({
            'success': True,
            'data': [safe.to_dict() for safe in safes]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/safes/<safe_id>')
def get_safe(safe_id):
    """API للحصول على خزينة محددة"""
    try:
        safe = TreasuryService.get_safe_by_id(safe_id)
        if not safe:
            return jsonify({
                'success': False,
                'message': 'الخزينة غير موجودة'
            }), 404
        
        return jsonify({
            'success': True,
            'data': safe.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/statistics')
def get_statistics():
    """API للحصول على الإحصائيات العامة"""
    try:
        stats = {
            'projects': {
                'total': len(ProjectService.get_all_projects()),
                'active': len(ProjectService.get_active_projects())
            },
            'customers': {
                'total': len(CustomerService.get_all_customers()),
                'active': len(CustomerService.get_active_customers())
            },
            'contracts': {
                'total': len(ContractService.get_all_contracts()),
                'active': len(ContractService.get_active_contracts())
            },
            'units': {
                'total': len(UnitService.get_all_units()),
                'available': len(UnitService.get_available_units()),
                'sold': len(UnitService.get_sold_units()),
                'reserved': len(UnitService.get_reserved_units())
            },
            'installments': {
                'pending': len(InstallmentService.get_pending_installments()),
                'overdue': len(InstallmentService.get_overdue_installments()),
                'paid': len(InstallmentService.get_paid_installments())
            },
            'treasury': {
                'total_safes': len(TreasuryService.get_all_safes()),
                'active_safes': len(TreasuryService.get_active_safes())
            }
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@api_bp.route('/search')
def search():
    """API للبحث العام"""
    try:
        search_term = request.args.get('q', '').strip()
        
        if not search_term:
            return jsonify({
                'success': False,
                'message': 'مصطلح البحث مطلوب'
            }), 400
        
        results = {
            'projects': [project.to_dict() for project in ProjectService.search_projects(search_term)],
            'customers': [customer.to_dict() for customer in CustomerService.search_customers(search_term)],
            'contracts': [contract.to_dict() for contract in ContractService.search_contracts(search_term)],
            'units': [unit.to_dict() for unit in UnitService.search_units(search_term)]
        }
        
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500