import random
import string
from datetime import datetime
from flask import current_app
from acc.extensions import db
from acc.models.audit import AuditLog


def generate_uid(prefix):
    """Generate unique ID similar to the original app"""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))
    return f"{prefix}-{suffix}"


def log_action(description, details=None, user_id=None):
    """Log an action to the audit log"""
    audit_entry = AuditLog(
        id=generate_uid('LOG'),
        description=description,
        details=details or {},
        user_id=user_id
    )
    db.session.add(audit_entry)
    # Don't commit here, let the calling function handle the transaction


def format_currency(amount):
    """Format amount as currency"""
    if amount is None:
        return "0.00 ج.م"
    return f"{amount:,.2f} ج.م"


def format_date(date_obj):
    """Format date object for display"""
    if date_obj is None:
        return "-"
    
    if isinstance(date_obj, str):
        return date_obj
    
    try:
        return date_obj.strftime('%Y-%m-%d')
    except:
        return str(date_obj)


def parse_number(value):
    """Parse a number from string, handling Arabic/English formats"""
    if not value:
        return 0
    
    # Convert Arabic numerals to English
    arabic_to_english = {
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    }
    
    value_str = str(value)
    for ar, en in arabic_to_english.items():
        value_str = value_str.replace(ar, en)
    
    # Remove non-numeric characters except dots
    value_str = ''.join(c for c in value_str if c.isdigit() or c == '.')
    
    try:
        return float(value_str) if value_str else 0
    except ValueError:
        return 0


def get_today():
    """Get today's date as string"""
    return datetime.now().strftime('%Y-%m-%d')


class Pagination:
    """Custom pagination class"""
    def __init__(self, query, page, per_page=20):
        self.query = query
        self.page = page
        self.per_page = per_page
        self.total = query.count()
        
    @property
    def items(self):
        return self.query.limit(self.per_page).offset((self.page - 1) * self.per_page).all()
    
    @property
    def prev_num(self):
        return self.page - 1 if self.has_prev else None
    
    @property
    def next_num(self):
        return self.page + 1 if self.has_next else None
    
    @property
    def has_prev(self):
        return self.page > 1
    
    @property
    def has_next(self):
        return self.page < self.pages
    
    @property
    def pages(self):
        return max(1, (self.total + self.per_page - 1) // self.per_page)
    
    @property
    def first(self):
        return (self.page - 1) * self.per_page + 1
    
    @property
    def last(self):
        return min(self.total, self.page * self.per_page)
    
    def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (self.page - left_current - 1 < num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num