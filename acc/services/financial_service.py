from acc.extensions import db
from acc.models import Voucher, Installment
from sqlalchemy import func
from decimal import Decimal

def get_contract_financials(contract):
    """
    Calculates the financial summary for a given contract.

    Returns a dictionary with:
    - total_value
    - total_paid
    - total_remaining
    - maintenance_paid
    - maintenance_remaining
    """

    # --- Total Value ---
    total_value = Decimal(contract.total_price)

    # --- Total Paid ---
    # Sum all receipt vouchers linked to this contract or its installments
    installment_ids = [inst.id for inst in contract.installments]

    total_paid_query = db.session.query(func.sum(Voucher.amount)).filter(
        Voucher.type == 'receipt',
        db.or_(
            Voucher.linked_ref == contract.id,
            Voucher.linked_ref.in_(installment_ids)
        )
    )
    total_paid = total_paid_query.scalar() or Decimal(0)

    # --- Maintenance Calculations ---
    maintenance_installment = next((inst for inst in contract.installments if inst.type == 'دفعة صيانة'), None)
    maintenance_paid = Decimal(0)
    maintenance_remaining = Decimal(0)

    if maintenance_installment:
        original_maintenance_amount = Decimal(maintenance_installment.original_amount or 0)
        remaining_maintenance_amount = Decimal(maintenance_installment.amount or 0)
        maintenance_paid = original_maintenance_amount - remaining_maintenance_amount
        maintenance_remaining = remaining_maintenance_amount

    # --- Total Remaining ---
    total_remaining = total_value - total_paid

    return {
        'total_value': total_value,
        'total_paid': total_paid,
        'total_remaining': total_remaining,
        'maintenance_paid': maintenance_paid,
        'maintenance_remaining': maintenance_remaining
    }
