"""
Generic CRUD service for all entities
"""
from flask import render_template, request, redirect, url_for, flash, jsonify
from acc.extensions import db
from acc.services.utils import generate_uid, log_action, Pagination, format_currency
from acc.services.code_generator import *
from sqlalchemy import or_, func
import json
import csv
import io
from datetime import datetime

class CRUDService:
    """Generic CRUD service for entities"""
    
    def __init__(self, model, entity_name, entity_title, code_generator=None):
        self.model = model
        self.entity_name = entity_name
        self.entity_title = entity_title
        self.code_generator = code_generator
    
    def get_search_query(self, query, search_term):
        """Override this method to customize search"""
        # Default search in name field
        if hasattr(self.model, 'name'):
            return query.filter(self.model.name.contains(search_term))
        return query
    
    def get_list_columns(self):
        """Define columns for list view"""
        return [
            {'key': 'code', 'label': 'الكود', 'type': 'text'},
            {'key': 'name', 'label': 'الاسم', 'type': 'link'},
            {'key': 'status', 'label': 'الحالة', 'type': 'status'},
        ]
    
    def index(self):
        """List all entities"""
        page = request.args.get('page', 1, type=int)
        q = request.args.get('q', '')
        
        query = self.model.query
        
        if q:
            query = self.get_search_query(query, q)
        
        query = query.order_by(self.model.name if hasattr(self.model, 'name') else self.model.id)
        pagination = Pagination(query, page)
        
        return render_template('shared/entity_list.html',
                             title=self.entity_title,
                             entity_name=self.entity_name,
                             add_button_text=f'إضافة {self.entity_title[:-1]}',
                             search_placeholder=f'بحث في {self.entity_title}...',
                             columns=self.get_list_columns(),
                             items=pagination.items,
                             pagination=pagination,
                             q=q,
                             has_detail=True,
                             has_report=True,
                             empty_icon='fas fa-box-open',
                             empty_message=f'لا يوجد {self.entity_title} حالياً',
                             format_currency=format_currency)
    
    def add(self):
        """Add new entity"""
        if request.method == 'POST':
            try:
                # Get form data
                data = self.get_form_data()
                
                # Validate
                errors = self.validate_data(data)
                if errors:
                    for error in errors:
                        flash(error, 'error')
                    return redirect(url_for(f'{self.entity_name}.add'))
                
                # Create entity
                entity = self.create_entity(data)
                
                db.session.add(entity)
                db.session.commit()
                
                # Log action
                log_action(f'إضافة {self.entity_title[:-1]}', {'id': entity.id, 'name': getattr(entity, 'name', entity.id)})
                
                flash(f'✅ تم إضافة {self.entity_title[:-1]} بنجاح', 'success')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': True,
                        'message': f'تم إضافة {self.entity_title[:-1]} بنجاح',
                        'redirect': url_for(f'{self.entity_name}.index')
                    })
                
                return redirect(url_for(f'{self.entity_name}.index'))
                
            except Exception as e:
                db.session.rollback()
                error_msg = f'❌ خطأ في إضافة {self.entity_title[:-1]}: {str(e)}'
                flash(error_msg, 'error')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': error_msg}), 500
                    
                return redirect(url_for(f'{self.entity_name}.add'))
        
        return render_template(f'{self.entity_name}/add.html')
    
    def edit(self, id):
        """Edit entity"""
        entity = self.model.query.get_or_404(id)
        
        if request.method == 'POST':
            try:
                # Get form data
                data = self.get_form_data()
                
                # Validate
                errors = self.validate_data(data, entity)
                if errors:
                    for error in errors:
                        flash(error, 'error')
                    return redirect(url_for(f'{self.entity_name}.edit', id=id))
                
                # Update entity
                self.update_entity(entity, data)
                
                db.session.commit()
                
                # Log action
                log_action(f'تعديل {self.entity_title[:-1]}', {'id': entity.id, 'name': getattr(entity, 'name', entity.id)})
                
                flash(f'✅ تم تحديث {self.entity_title[:-1]} بنجاح', 'success')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': True,
                        'message': f'تم تحديث {self.entity_title[:-1]} بنجاح',
                        'redirect': url_for(f'{self.entity_name}.detail', id=id)
                    })
                
                return redirect(url_for(f'{self.entity_name}.detail', id=id))
                
            except Exception as e:
                db.session.rollback()
                error_msg = f'❌ خطأ في تحديث {self.entity_title[:-1]}: {str(e)}'
                flash(error_msg, 'error')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': error_msg}), 500
                    
                return redirect(url_for(f'{self.entity_name}.edit', id=id))
        
        return render_template(f'{self.entity_name}/edit.html', entity=entity)
    
    def delete(self, id):
        """Delete entity"""
        try:
            entity = self.model.query.get_or_404(id)
            
            # Check if can delete
            error = self.check_delete_constraints(entity)
            if error:
                flash(error, 'error')
                return redirect(url_for(f'{self.entity_name}.index'))
            
            # Store info before deletion
            entity_name = getattr(entity, 'name', entity.id)
            entity_id = entity.id
            
            # Delete
            db.session.delete(entity)
            db.session.commit()
            
            # Log action
            log_action(f'حذف {self.entity_title[:-1]}', {'id': entity_id, 'name': entity_name})
            
            flash(f'✅ تم حذف {self.entity_title[:-1]} "{entity_name}" بنجاح', 'success')
            return redirect(url_for(f'{self.entity_name}.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ خطأ في حذف {self.entity_title[:-1]}: {str(e)}', 'error')
            return redirect(url_for(f'{self.entity_name}.index'))
    
    def export(self, format):
        """Export entities"""
        entities = self.model.query.order_by(self.model.name if hasattr(self.model, 'name') else self.model.id).all()
        
        if format == 'excel':
            return self.export_excel(entities)
        elif format == 'json':
            return self.export_json(entities)
        elif format == 'csv':
            return self.export_csv(entities)
        else:
            flash('صيغة التصدير غير مدعومة', 'error')
            return redirect(url_for(f'{self.entity_name}.index'))
    
    def export_excel(self, entities):
        """Export to Excel HTML"""
        from flask import make_response
        
        columns = self.get_export_columns()
        
        html = self.generate_excel_html(self.entity_title, columns, entities)
        
        response = make_response(html)
        response.headers['Content-Type'] = 'application/vnd.ms-excel; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename={self.entity_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls'
        
        return response
    
    def export_json(self, entities):
        """Export to JSON"""
        from flask import make_response
        
        data = [self.entity_to_dict(e) for e in entities]
        response = make_response(json.dumps(data, ensure_ascii=False, indent=2))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename={self.entity_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        return response
    
    def export_csv(self, entities):
        """Export to CSV"""
        from flask import make_response
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        columns = self.get_export_columns()
        writer.writerow([col['label'] for col in columns])
        
        # Data
        for entity in entities:
            row = []
            for col in columns:
                value = getattr(entity, col['key'], '')
                if col.get('type') == 'date' and value:
                    value = value.strftime('%Y-%m-%d')
                row.append(value or '')
            writer.writerow(row)
        
        response = make_response('\ufeff' + output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
        response.headers['Content-Disposition'] = f'attachment; filename={self.entity_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
    
    # Methods to override in subclasses
    def get_form_data(self):
        """Get data from form"""
        raise NotImplementedError
    
    def validate_data(self, data, entity=None):
        """Validate form data"""
        errors = []
        if not data.get('name'):
            errors.append(f'❌ الرجاء إدخال اسم {self.entity_title[:-1]}')
        return errors
    
    def create_entity(self, data):
        """Create new entity from data"""
        raise NotImplementedError
    
    def update_entity(self, entity, data):
        """Update entity with data"""
        raise NotImplementedError
    
    def check_delete_constraints(self, entity):
        """Check if entity can be deleted"""
        return None
    
    def get_export_columns(self):
        """Get columns for export"""
        return [
            {'key': 'code', 'label': 'الكود'},
            {'key': 'name', 'label': 'الاسم'},
            {'key': 'status', 'label': 'الحالة'},
            {'key': 'created_at', 'label': 'تاريخ التسجيل', 'type': 'date'},
        ]
    
    def entity_to_dict(self, entity):
        """Convert entity to dictionary"""
        return {
            'id': entity.id,
            'code': getattr(entity, 'code', ''),
            'name': getattr(entity, 'name', ''),
            'status': getattr(entity, 'status', ''),
            'created_at': entity.created_at.isoformat() if hasattr(entity, 'created_at') and entity.created_at else None
        }
    
    def generate_excel_html(self, title, columns, entities):
        """Generate Excel HTML"""
        html = f'''
        <html xmlns:o="urn:schemas-microsoft-com:office:office"
              xmlns:x="urn:schemas-microsoft-com:office:excel"
              xmlns="http://www.w3.org/TR/REC-html40">
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            <style>
                table {{
                    border-collapse: collapse;
                    width: 100%;
                }}
                th {{
                    background-color: #366092;
                    color: white;
                    font-weight: bold;
                    padding: 10px;
                    text-align: right;
                    border: 1px solid #ddd;
                }}
                td {{
                    padding: 8px;
                    text-align: right;
                    border: 1px solid #ddd;
                }}
                tr:nth-child(even) {{
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <table>
                <thead>
                    <tr>
        '''
        
        for col in columns:
            html += f'<th>{col["label"]}</th>'
        
        html += '''
                    </tr>
                </thead>
                <tbody>
        '''
        
        for entity in entities:
            html += '<tr>'
            for col in columns:
                value = getattr(entity, col['key'], '')
                if col.get('type') == 'date' and value:
                    value = value.strftime('%Y-%m-%d')
                html += f'<td>{value or ""}</td>'
            html += '</tr>'
        
        html += '''
                </tbody>
            </table>
        </body>
        </html>
        '''
        
        return html