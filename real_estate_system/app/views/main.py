from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app.services.project_service import ProjectService
from app.services.customer_service import CustomerService
from app.services.contract_service import ContractService
from app.services.unit_service import UnitService
from app.services.installment_service import InstallmentService
from app.services.treasury_service import TreasuryService
from app.services.utils import paginate_query

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """الصفحة الرئيسية"""
    try:
        # إحصائيات عامة
        stats = {
            'total_projects': len(ProjectService.get_all_projects()),
            'active_projects': len(ProjectService.get_active_projects()),
            'total_customers': len(CustomerService.get_all_customers()),
            'active_customers': len(CustomerService.get_active_customers()),
            'total_contracts': len(ContractService.get_all_contracts()),
            'active_contracts': len(ContractService.get_active_contracts()),
            'total_units': len(UnitService.get_all_units()),
            'available_units': len(UnitService.get_available_units()),
            'sold_units': len(UnitService.get_sold_units()),
            'pending_installments': len(InstallmentService.get_pending_installments()),
            'overdue_installments': len(InstallmentService.get_overdue_installments()),
            'total_safes': len(TreasuryService.get_all_safes())
        }
        
        # المشاريع النشطة
        active_projects = ProjectService.get_active_projects()
        
        # العقود الأخيرة
        recent_contracts = ContractService.get_all_contracts()[:5]
        
        # الأقساط المتأخرة
        overdue_installments = InstallmentService.get_overdue_installments()[:5]
        
        return render_template('main/index.html', 
                             stats=stats,
                             active_projects=active_projects,
                             recent_contracts=recent_contracts,
                             overdue_installments=overdue_installments)
    except Exception as e:
        flash(f'خطأ في تحميل الصفحة الرئيسية: {str(e)}', 'error')
        return render_template('main/index.html', 
                             stats={},
                             active_projects=[],
                             recent_contracts=[],
                             overdue_installments=[])


@bp.route('/search')
def search():
    """البحث العام"""
    search_term = request.args.get('q', '').strip()
    
    if not search_term:
        return jsonify({
            'success': False,
            'message': 'يرجى إدخال مصطلح البحث'
        })
    
    try:
        results = {
            'projects': ProjectService.search_projects(search_term),
            'customers': CustomerService.search_customers(search_term),
            'contracts': ContractService.search_contracts(search_term),
            'units': UnitService.search_units(search_term)
        }
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في البحث: {str(e)}'
        })


@bp.route('/dashboard')
def dashboard():
    """لوحة التحكم"""
    try:
        # إحصائيات مفصلة
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
        
        # أفضل العملاء
        top_customers = CustomerService.get_top_customers_by_value(5)
        
        # العملاء الذين لديهم أقساط متأخرة
        customers_with_overdue = CustomerService.get_customers_with_overdue_payments()
        
        # العقود التي لديها أقساط متأخرة
        contracts_with_overdue = ContractService.get_contracts_with_overdue_installments()
        
        return render_template('main/dashboard.html',
                             stats=stats,
                             top_customers=top_customers,
                             customers_with_overdue=customers_with_overdue,
                             contracts_with_overdue=contracts_with_overdue)
    except Exception as e:
        flash(f'خطأ في تحميل لوحة التحكم: {str(e)}', 'error')
        return render_template('main/dashboard.html',
                             stats={},
                             top_customers=[],
                             customers_with_overdue=[],
                             contracts_with_overdue=[])


@bp.route('/reports')
def reports():
    """التقارير"""
    try:
        # إحصائيات التقارير
        report_stats = {
            'financial_summary': ContractService.get_contracts_financial_summary(),
            'projects_summary': {},
            'customers_summary': {},
            'units_summary': {}
        }
        
        # ملخص المشاريع
        for project in ProjectService.get_active_projects():
            report_stats['projects_summary'][project.id] = ProjectService.get_project_statistics(project.id)
        
        # ملخص العملاء
        for customer in CustomerService.get_active_customers()[:10]:  # أفضل 10 عملاء
            report_stats['customers_summary'][customer.id] = CustomerService.get_customer_statistics(customer.id)
        
        # ملخص الوحدات
        for project in ProjectService.get_active_projects():
            report_stats['units_summary'][project.id] = UnitService.get_project_units_summary(project.id)
        
        return render_template('main/reports.html', report_stats=report_stats)
    except Exception as e:
        flash(f'خطأ في تحميل التقارير: {str(e)}', 'error')
        return render_template('main/reports.html', report_stats={})


@bp.route('/settings')
def settings():
    """الإعدادات"""
    try:
        # إعدادات النظام
        from app.models import Settings
        
        system_settings = {
            'site_name': Settings.get_setting('site_name', 'نظام إدارة العقارات'),
            'default_currency': Settings.get_setting('default_currency', 'ريال'),
            'items_per_page': Settings.get_setting('items_per_page', '20'),
            'backup_enabled': Settings.get_setting('backup_enabled', 'true'),
            'backup_frequency': Settings.get_setting('backup_frequency', 'daily')
        }
        
        return render_template('main/settings.html', settings=system_settings)
    except Exception as e:
        flash(f'خطأ في تحميل الإعدادات: {str(e)}', 'error')
        return render_template('main/settings.html', settings={})


@bp.route('/settings', methods=['POST'])
def update_settings():
    """تحديث الإعدادات"""
    try:
        from app.models import Settings
        
        # تحديث الإعدادات
        Settings.set_setting('site_name', request.form.get('site_name'))
        Settings.set_setting('default_currency', request.form.get('default_currency'))
        Settings.set_setting('items_per_page', request.form.get('items_per_page'))
        Settings.set_setting('backup_enabled', request.form.get('backup_enabled'))
        Settings.set_setting('backup_frequency', request.form.get('backup_frequency'))
        
        flash('تم تحديث الإعدادات بنجاح', 'success')
        return redirect(url_for('main.settings'))
    except Exception as e:
        flash(f'خطأ في تحديث الإعدادات: {str(e)}', 'error')
        return redirect(url_for('main.settings'))


@bp.route('/help')
def help():
    """المساعدة"""
    return render_template('main/help.html')


@bp.route('/about')
def about():
    """حول النظام"""
    return render_template('main/about.html')