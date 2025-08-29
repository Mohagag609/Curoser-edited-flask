"""
Automatic code generation service
"""
from acc.extensions import db
from sqlalchemy import func

def get_next_code(model, prefix, digits=3):
    """
    Generate next sequential code for a model
    
    Args:
        model: The SQLAlchemy model class
        prefix: The prefix for the code (e.g., 'C' for Customer)
        digits: Number of digits for the numeric part
    
    Returns:
        str: The next code (e.g., 'C001')
    """
    # Get the last code from database
    last_record = db.session.query(model).order_by(model.id.desc()).first()
    
    if not last_record or not last_record.code:
        # First record
        next_number = 1
    else:
        # Extract number from last code
        try:
            # Remove prefix and get number
            last_code = last_record.code
            if last_code.startswith(prefix):
                number_part = last_code[len(prefix):]
                next_number = int(number_part) + 1
            else:
                next_number = 1
        except (ValueError, AttributeError):
            next_number = 1
    
    # Format code with leading zeros
    code = f"{prefix}{str(next_number).zfill(digits)}"
    
    # Check if code already exists (in case of manual entries)
    while db.session.query(model).filter_by(code=code).first():
        next_number += 1
        code = f"{prefix}{str(next_number).zfill(digits)}"
    
    return code

def generate_customer_code():
    """Generate next customer code (C001, C002, etc.)"""
    from acc.models import Customer
    return get_next_code(Customer, 'C', 3)

def generate_supplier_code():
    """Generate next supplier code (S001, S002, etc.)"""
    from acc.models import Supplier
    return get_next_code(Supplier, 'S', 3)

def generate_contractor_code():
    """Generate next contractor code (CON001, CON002, etc.)"""
    from acc.models import Contractor
    return get_next_code(Contractor, 'CON', 3)

def generate_partner_code():
    """Generate next partner code (P001, P002, etc.)"""
    from acc.models import Partner
    return get_next_code(Partner, 'P', 3)

def generate_broker_code():
    """Generate next broker code (B001, B002, etc.)"""
    from acc.models import Broker
    return get_next_code(Broker, 'B', 3)

def generate_material_code():
    """Generate next material code (M001, M002, etc.)"""
    from acc.models import Material
    return get_next_code(Material, 'M', 3)

def generate_safe_code():
    """Generate next safe code (SF001, SF002, etc.)"""
    from acc.models import Safe
    # Safe uses 'name' instead of 'code'
    last_safe = db.session.query(Safe).filter(
        Safe.name.like('SF%')
    ).order_by(Safe.id.desc()).first()
    
    if not last_safe:
        return 'SF001'
    
    try:
        # Extract number from name
        name = last_safe.name
        if name.startswith('SF'):
            number_part = name[2:]
            next_number = int(number_part) + 1
        else:
            next_number = 1
    except (ValueError, AttributeError):
        next_number = 1
    
    # Format code
    code = f"SF{str(next_number).zfill(3)}"
    
    # Check if exists
    while db.session.query(Safe).filter_by(name=code).first():
        next_number += 1
        code = f"SF{str(next_number).zfill(3)}"
    
    return code

def generate_unit_code(building, floor, unit_name):
    """
    Generate unit code from building, floor and unit name
    Example: Building A, Floor 3, Unit 5 => A-3-5
    """
    # Clean inputs
    building = str(building).strip().upper()
    floor = str(floor).strip()
    unit_name = str(unit_name).strip()
    
    # Extract unit number if possible
    import re
    unit_match = re.search(r'\d+', unit_name)
    unit_num = unit_match.group() if unit_match else unit_name[:3].upper()
    
    # Generate code
    code = f"{building}-{floor}-{unit_num}"
    
    # Check uniqueness
    from acc.models import Unit
    base_code = code
    counter = 1
    
    while db.session.query(Unit).filter_by(code=code).first():
        code = f"{base_code}-{counter}"
        counter += 1
    
    return code

def generate_contract_code():
    """Generate next contract code (CNT001, CNT002, etc.)"""
    from acc.models import Contract
    return get_next_code(Contract, 'CNT', 3)

def generate_project_code():
    """Generate next project code (PRJ001, PRJ002, etc.)"""
    from acc.models import Project
    return get_next_code(Project, 'PRJ', 3)

def generate_voucher_code(voucher_type):
    """
    Generate voucher code based on type
    Receipt: REC001, Payment: PAY001
    """
    from acc.models import Voucher
    prefix = 'REC' if voucher_type == 'receipt' else 'PAY'
    
    # Get last voucher of same type
    last_voucher = db.session.query(Voucher).filter(
        Voucher.type == voucher_type,
        Voucher.code.like(f'{prefix}%')
    ).order_by(Voucher.id.desc()).first()
    
    if not last_voucher:
        return f'{prefix}001'
    
    try:
        # Extract number
        code = last_voucher.code
        if code.startswith(prefix):
            number_part = code[len(prefix):]
            next_number = int(number_part) + 1
        else:
            next_number = 1
    except (ValueError, AttributeError):
        next_number = 1
    
    # Format code
    code = f"{prefix}{str(next_number).zfill(3)}"
    
    # Check if exists
    while db.session.query(Voucher).filter_by(code=code).first():
        next_number += 1
        code = f"{prefix}{str(next_number).zfill(3)}"
    
    return code