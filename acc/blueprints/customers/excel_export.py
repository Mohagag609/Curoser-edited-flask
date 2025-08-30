"""
Excel export functionality with basic HTML table as fallback
"""
from flask import make_response
from datetime import datetime

def export_excel_html(customers):
    """تصدير العملاء إلى Excel عبر HTML Table"""
    html = '''
    <html xmlns:o="urn:schemas-microsoft-com:office:office"
          xmlns:x="urn:schemas-microsoft-com:office:excel"
          xmlns="http://www.w3.org/TR/REC-html40">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <style>
            table {
                border-collapse: collapse;
                width: 100%;
            }
            th {
                background-color: #366092;
                color: white;
                font-weight: bold;
                padding: 10px;
                text-align: right;
                border: 1px solid #ddd;
            }
            td {
                padding: 8px;
                text-align: right;
                border: 1px solid #ddd;
            }
            tr:nth-child(even) {
                background-color: #f2f2f2;
            }
            .number {
                mso-number-format: "0";
            }
            .text {
                mso-number-format: "\@";
            }
        </style>
    </head>
    <body>
        <table>
            <thead>
                <tr>
                    <th>الكود</th>
                    <th>الاسم</th>
                    <th>الهاتف</th>
                    <th>الرقم القومي</th>
                    <th>العنوان</th>
                    <th>الحالة</th>
                    <th>ملاحظات</th>
                    <th>تاريخ التسجيل</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    for customer in customers:
        html += f'''
                <tr>
                    <td class="text">{customer.id}</td>
                    <td>{customer.name}</td>
                    <td class="text">{customer.phone or ''}</td>
                    <td class="text">{customer.national_id or ''}</td>
                    <td>{customer.address or ''}</td>
                    <td>{customer.status}</td>
                    <td>{customer.notes or ''}</td>
                    <td>{customer.created_at.strftime('%Y-%m-%d') if customer.created_at else ''}</td>
                </tr>
        '''
    
    html += '''
            </tbody>
        </table>
    </body>
    </html>
    '''
    
    response = make_response(html)
    response.headers['Content-Type'] = 'application/vnd.ms-excel; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=customers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls'
    
    return response

def export_report_excel(title, headers, rows, summary=None):
    """تصدير تقرير إلى Excel عبر HTML"""
    html = f'''
    <html xmlns:o="urn:schemas-microsoft-com:office:office"
          xmlns:x="urn:schemas-microsoft-com:office:excel"
          xmlns="http://www.w3.org/TR/REC-html40">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
            }}
            h1 {{
                color: #366092;
                text-align: center;
                margin-bottom: 20px;
            }}
            .summary {{
                margin-bottom: 30px;
                padding: 15px;
                background-color: #e8f4f8;
                border-radius: 5px;
            }}
            .summary-item {{
                display: inline-block;
                margin-right: 30px;
                font-weight: bold;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-top: 20px;
            }}
            th {{
                background-color: #366092;
                color: white;
                font-weight: bold;
                padding: 12px;
                text-align: right;
                border: 1px solid #ddd;
            }}
            td {{
                padding: 10px;
                text-align: right;
                border: 1px solid #ddd;
            }}
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            .number {{
                mso-number-format: "#,##0.00";
                text-align: left;
            }}
            .text {{
                mso-number-format: "\\@";
            }}
            .percentage {{
                mso-number-format: "0.00%";
                text-align: center;
            }}
            .positive {{
                color: green;
                font-weight: bold;
            }}
            .negative {{
                color: red;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
    '''
    
    # إضافة الملخص إن وجد
    if summary:
        html += '<div class="summary">'
        for key, value in summary.items():
            html += f'<span class="summary-item">{key}: {value}</span>'
        html += '</div>'
    
    # إضافة الجدول
    html += '<table><thead><tr>'
    for header in headers:
        html += f'<th>{header}</th>'
    html += '</tr></thead><tbody>'
    
    for row in rows:
        html += '<tr>'
        for i, cell in enumerate(row):
            cell_class = ''
            cell_value = cell
            
            # تحديد نوع البيانات
            if isinstance(cell, (int, float)):
                cell_class = 'number'
                if cell < 0:
                    cell_class += ' negative'
                elif cell > 0 and i > 0:  # ليس العمود الأول
                    cell_class += ' positive'
            elif '%' in str(cell):
                cell_class = 'percentage'
            elif i == 0:  # العمود الأول عادة نصي
                cell_class = 'text'
            
            html += f'<td class="{cell_class}">{cell_value}</td>'
        html += '</tr>'
    
    html += '''
            </tbody>
        </table>
    </body>
    </html>
    '''
    
    response = make_response(html)
    response.headers['Content-Type'] = 'application/vnd.ms-excel; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename={title.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls'
    
    return response