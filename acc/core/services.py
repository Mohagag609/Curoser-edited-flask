"""
نظام الخدمات الموحد والمحسن
"""
from flask import render_template, request, redirect, url_for, flash, jsonify
from acc.extensions import db
from acc.core.performance import performance_manager, monitor_performance
from acc.core.logging import log_action, log_error
from sqlalchemy import or_, func, desc
import json
import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional

class BaseService:
    """الخدمة الأساسية لجميع الكيانات"""
    
    def __init__(self, model, entity_name: str, entity_title: str):
        self.model = model
        self.entity_name = entity_name
        self.entity_title = entity_title
    
    @performance_manager.cached(timeout=300)
    def get_list_data(self, page: int = 1, per_page: int = 20, search: str = None, filters: Dict = None):
        """الحصول على قائمة البيانات مع التخزين المؤقت"""
        query = self.model.query
        
        # تطبيق البحث
        if search:
            query = self._apply_search(query, search)
        
        # تطبيق المرشحات
        if filters:
            query = self._apply_filters(query, filters)
        
        # ترتيب النتائج
        query = self._apply_ordering(query)
        
        # الصفحات
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return pagination
    
    def _apply_search(self, query, search_term: str):
        """تطبيق البحث - يمكن تخصيصه في كل خدمة"""
        if hasattr(self.model, 'name'):
            return query.filter(self.model.name.contains(search_term))
        return query
    
    def _apply_filters(self, query, filters: Dict):
        """تطبيق المرشحات - يمكن تخصيصه في كل خدمة"""
        for key, value in filters.items():
            if hasattr(self.model, key) and value:
                query = query.filter(getattr(self.model, key) == value)
        return query
    
    def _apply_ordering(self, query):
        """تطبيق الترتيب"""
        if hasattr(self.model, 'created_at'):
            return query.order_by(desc(self.model.created_at))
        elif hasattr(self.model, 'name'):
            return query.order_by(self.model.name)
        return query.order_by(self.model.id)
    
    @monitor_performance('create_entity')
    def create_entity(self, data: Dict) -> Any:
        """إنشاء كيان جديد"""
        try:
            entity = self.model(**data)
            db.session.add(entity)
            db.session.commit()
            
            log_action(f'created_{self.entity_name}', details=f'Created {self.entity_title}: {entity.id}')
            return entity
            
        except Exception as e:
            db.session.rollback()
            log_error(e, f'create_{self.entity_name}')
            raise
    
    @monitor_performance('update_entity')
    def update_entity(self, entity_id: str, data: Dict) -> Any:
        """تحديث كيان موجود"""
        try:
            entity = self.model.query.get_or_404(entity_id)
            
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            
            db.session.commit()
            
            log_action(f'updated_{self.entity_name}', details=f'Updated {self.entity_title}: {entity_id}')
            return entity
            
        except Exception as e:
            db.session.rollback()
            log_error(e, f'update_{self.entity_name}')
            raise
    
    @monitor_performance('delete_entity')
    def delete_entity(self, entity_id: str) -> bool:
        """حذف كيان"""
        try:
            entity = self.model.query.get_or_404(entity_id)
            db.session.delete(entity)
            db.session.commit()
            
            log_action(f'deleted_{self.entity_name}', details=f'Deleted {self.entity_title}: {entity_id}')
            return True
            
        except Exception as e:
            db.session.rollback()
            log_error(e, f'delete_{self.entity_name}')
            raise
    
    def export_to_csv(self, entities: List[Any], filename: str = None) -> str:
        """تصدير البيانات إلى CSV"""
        if not filename:
            filename = f"{self.entity_name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # كتابة العناوين
        headers = self._get_export_headers()
        writer.writerow(headers)
        
        # كتابة البيانات
        for entity in entities:
            row = self._get_export_row(entity)
            writer.writerow(row)
        
        return output.getvalue()
    
    def _get_export_headers(self) -> List[str]:
        """الحصول على عناوين التصدير"""
        return ['ID', 'Name', 'Created At']
    
    def _get_export_row(self, entity: Any) -> List[str]:
        """الحصول على صف التصدير"""
        return [
            str(entity.id),
            getattr(entity, 'name', ''),
            str(getattr(entity, 'created_at', ''))
        ]

class CustomerService(BaseService):
    """خدمة العملاء المحسنة"""
    
    def __init__(self):
        from acc.models import Customer
        super().__init__(Customer, 'customer', 'عميل')
    
    def _apply_search(self, query, search_term: str):
        """بحث متقدم في العملاء"""
        return query.filter(
            or_(
                self.model.name.contains(search_term),
                self.model.phone.contains(search_term),
                self.model.national_id.contains(search_term),
                self.model.code.contains(search_term)
            )
        )
    
    def _apply_filters(self, query, filters: Dict):
        """مرشحات العملاء"""
        if 'status' in filters and filters['status']:
            query = query.filter(self.model.status == filters['status'])
        if 'project_id' in filters and filters['project_id']:
            query = query.filter(self.model.project_id == filters['project_id'])
        return query
    
    def get_customer_stats(self, project_id: str = None) -> Dict:
        """إحصائيات العملاء"""
        query = self.model.query
        if project_id:
            query = query.filter_by(project_id=project_id)
        
        total = query.count()
        active = query.filter_by(status='نشط').count()
        inactive = query.filter_by(status='غير نشط').count()
        
        return {
            'total': total,
            'active': active,
            'inactive': inactive,
            'active_percentage': (active / total * 100) if total > 0 else 0
        }
    
    def _get_export_headers(self) -> List[str]:
        """عناوين تصدير العملاء"""
        return ['الكود', 'الاسم', 'الهاتف', 'الرقم القومي', 'الحالة', 'تاريخ الإنشاء']
    
    def _get_export_row(self, entity: Any) -> List[str]:
        """صف تصدير العميل"""
        return [
            str(entity.code),
            str(entity.name),
            str(entity.phone),
            str(entity.national_id),
            str(entity.status),
            str(entity.created_at)
        ]

class ContractService(BaseService):
    """خدمة العقود المحسنة"""
    
    def __init__(self):
        from acc.models import Contract
        super().__init__(Contract, 'contract', 'عقد')
    
    def _apply_search(self, query, search_term: str):
        """بحث في العقود"""
        return query.join(self.model.customer).filter(
            or_(
                self.model.code.contains(search_term),
                self.model.customer.has(name=search_term)
            )
        )
    
    def _apply_filters(self, query, filters: Dict):
        """مرشحات العقود"""
        if 'status' in filters and filters['status']:
            query = query.filter(self.model.status == filters['status'])
        if 'payment_type' in filters and filters['payment_type']:
            query = query.filter(self.model.payment_type == filters['payment_type'])
        if 'project_id' in filters and filters['project_id']:
            query = query.filter(self.model.project_id == filters['project_id'])
        return query
    
    def get_contract_stats(self, project_id: str = None) -> Dict:
        """إحصائيات العقود"""
        query = self.model.query
        if project_id:
            query = query.filter_by(project_id=project_id)
        
        total = query.count()
        active = query.filter_by(status='نشط').count()
        completed = query.filter_by(status='مكتمل').count()
        total_value = query.with_entities(func.sum(self.model.total_price)).scalar() or 0
        
        return {
            'total': total,
            'active': active,
            'completed': completed,
            'total_value': float(total_value),
            'completion_rate': (completed / total * 100) if total > 0 else 0
        }
    
    def create_contract_with_installments(self, contract_data: Dict) -> Any:
        """إنشاء عقد مع أقساطه"""
        try:
            # إنشاء العقد
            contract = self.create_entity(contract_data)
            
            # حساب السعر الصافي
            contract.calculate_net_price()
            
            # إنشاء الأقساط إذا كان الدفع بالأقساط
            if contract.payment_type == 'أقساط':
                contract.generate_installments()
            
            db.session.commit()
            return contract
            
        except Exception as e:
            db.session.rollback()
            log_error(e, 'create_contract_with_installments')
            raise

class InstallmentService(BaseService):
    """خدمة الأقساط المحسنة"""
    
    def __init__(self):
        from acc.models import Installment
        super().__init__(Installment, 'installment', 'قسط')
    
    def _apply_filters(self, query, filters: Dict):
        """مرشحات الأقساط"""
        if 'status' in filters and filters['status']:
            query = query.filter(self.model.status == filters['status'])
        if 'project_id' in filters and filters['project_id']:
            query = query.filter(self.model.project_id == filters['project_id'])
        if 'is_overdue' in filters and filters['is_overdue']:
            query = query.filter(self.model.is_overdue == True)
        return query
    
    def get_overdue_installments(self, project_id: str = None) -> List[Any]:
        """الحصول على الأقساط المتأخرة"""
        return self.model.get_overdue_installments(project_id)
    
    def get_due_installments(self, project_id: str = None, days_ahead: int = 7) -> List[Any]:
        """الحصول على الأقساط المستحقة"""
        return self.model.get_due_installments(project_id, days_ahead)
    
    def process_payment(self, installment_id: str, amount: float, payment_date: str = None) -> bool:
        """معالجة دفعة للقسط"""
        try:
            installment = self.model.query.get_or_404(installment_id)
            installment.add_payment(amount, payment_date)
            
            log_action('installment_payment', details=f'Payment of {amount} for installment {installment_id}')
            return True
            
        except Exception as e:
            log_error(e, 'process_payment')
            raise

# مثيلات الخدمات
customer_service = CustomerService()
contract_service = ContractService()
installment_service = InstallmentService()