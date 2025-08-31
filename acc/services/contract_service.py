from acc.extensions import db
from acc.models import Installment
from decimal import Decimal
from dateutil.relativedelta import relativedelta

def generate_installments_for_contract(contract):
    """
    Generates and saves installment records for a given contract.
    This function should be called after a contract has been committed to the DB.
    """

    # Clear any existing installments for this contract to prevent duplication
    Installment.query.filter_by(contract_id=contract.id).delete()

    # Do not generate installments for cash deals
    if contract.payment_type == 'cash':
        return

    # --- Calculations ---
    total_price = Decimal(contract.total_price)
    down_payment = Decimal(contract.down_payment)
    discount = Decimal(contract.discount_amount)
    maintenance = Decimal(contract.maintenance_deposit)

    # The amount that is subject to installments
    installment_base_amount = total_price - maintenance

    # The remaining amount after down payment and discount
    total_after_down_payment = installment_base_amount - down_payment - discount

    # Value of all special annual payments
    total_annual_payments_value = Decimal(contract.extra_annual) * Decimal(contract.annual_payment_value)

    if total_after_down_payment < 0:
        raise ValueError("Down payment and discount exceed the installment amount.")
    if total_annual_payments_value > total_after_down_payment:
        raise ValueError("Annual payments value exceeds the remaining amount.")

    # The amount to be distributed over regular installments
    amount_for_regular_installments = total_after_down_payment - total_annual_payments_value

    start_date = contract.start_date
    installments_to_add = []

    # --- Generate Regular Installments ---
    if contract.installment_count > 0 and amount_for_regular_installments > 0:
        months_period = {
            'شهري': 1,
            'ربع سنوي': 3,
            'نصف سنوي': 6,
            'سنوي': 12
        }.get(contract.installment_type, 1)

        # Calculate base amount and round to 2 decimal places
        base_amount = round(amount_for_regular_installments / contract.installment_count, 2)
        accumulated_amount = Decimal(0)

        for i in range(contract.installment_count):
            due_date = start_date + relativedelta(months=months_period * (i + 1))

            # For the last installment, assign the remainder to avoid rounding errors
            amount = base_amount
            if i == contract.installment_count - 1:
                amount = amount_for_regular_installments - accumulated_amount

            accumulated_amount += amount

            inst = Installment(
                id=f"INST-{contract.code}-{i+1}",
                contract_id=contract.id,
                unit_id=contract.unit_id,
                installment_number=i + 1,
                type=contract.installment_type,
                original_amount=amount,
                amount=amount, # Initially, remaining amount is the full amount
                due_date=due_date,
                status='غير مدفوع'
            )
            installments_to_add.append(inst)

    # --- Generate Annual Bonus Installments ---
    if contract.extra_annual > 0 and contract.annual_payment_value > 0:
        for j in range(contract.extra_annual):
            due_date = start_date + relativedelta(years=j + 1)
            inst = Installment(
                id=f"INST-{contract.code}-A{j+1}",
                contract_id=contract.id,
                unit_id=contract.unit_id,
                installment_number=j + 1,
                type='دفعة سنوية',
                original_amount=contract.annual_payment_value,
                amount=contract.annual_payment_value,
                due_date=due_date,
                status='غير مدفوع'
            )
            installments_to_add.append(inst)

    # --- Generate Maintenance Deposit Installment ---
    if maintenance > 0:
        # Find the last due date from all generated installments
        if installments_to_add:
            last_due_date = max(inst.due_date for inst in installments_to_add)
            maintenance_due_date = last_due_date + relativedelta(months=1) # 1 month after the last installment
        else:
            # If no other installments, make it due 1 month after contract start
            maintenance_due_date = start_date + relativedelta(months=1)

        inst = Installment(
            id=f"INST-{contract.code}-M",
            contract_id=contract.id,
            unit_id=contract.unit_id,
            type='دفعة صيانة',
            original_amount=maintenance,
            amount=maintenance,
            due_date=maintenance_due_date,
            status='غير مدفوع'
        )
        installments_to_add.append(inst)

    if installments_to_add:
        db.session.bulk_save_objects(installments_to_add)
        db.session.commit()
