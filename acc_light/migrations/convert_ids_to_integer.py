"""
Script to convert all string IDs to integer IDs with autoincrement
This will create new migration files to handle the conversion properly
"""

import os

# Define all tables and their relationships
TABLES = {
    'customers': {
        'references': [],
        'referenced_by': [('contracts', 'customer_id'), ('vouchers', 'entity_id')]
    },
    'suppliers': {
        'references': [],
        'referenced_by': [('project_materials', 'supplier_id'), ('vouchers', 'entity_id')]
    },
    'contractors': {
        'references': [],
        'referenced_by': [('project_stages', 'contractor_id'), ('vouchers', 'entity_id')]
    },
    'partners': {
        'references': [],
        'referenced_by': [
            ('partner_group_members', 'partner_id'),
            ('unit_partners', 'partner_id'),
            ('partner_debts', 'creditor_id'),
            ('partner_debts', 'debtor_id'),
            ('vouchers', 'entity_id')
        ]
    },
    'partner_groups': {
        'references': [],
        'referenced_by': [('partner_group_members', 'group_id')]
    },
    'brokers': {
        'references': [],
        'referenced_by': [('broker_dues', 'broker_id')]
    },
    'projects': {
        'references': [],
        'referenced_by': [
            ('units', 'project_id'),
            ('contracts', 'project_id'),
            ('safes', 'project_id'),
            ('vouchers', 'project_id'),
            ('project_stages', 'project_id'),
            ('project_materials', 'project_id')
        ]
    },
    'units': {
        'references': [('projects', 'project_id')],
        'referenced_by': [
            ('contracts', 'unit_id'),
            ('unit_partners', 'unit_id'),
            ('partner_debts', 'unit_id')
        ]
    },
    'contracts': {
        'references': [
            ('customers', 'customer_id'),
            ('units', 'unit_id'),
            ('projects', 'project_id'),
            ('safes', 'commission_safe_id')
        ],
        'referenced_by': [('installments', 'contract_id')]
    },
    'installments': {
        'references': [
            ('contracts', 'contract_id'),
            ('units', 'unit_id')
        ],
        'referenced_by': []
    },
    'safes': {
        'references': [('projects', 'project_id')],
        'referenced_by': [
            ('vouchers', 'safe_id'),
            ('safe_transfers', 'from_safe_id'),
            ('safe_transfers', 'to_safe_id'),
            ('contracts', 'commission_safe_id')
        ]
    },
    'vouchers': {
        'references': [
            ('safes', 'safe_id'),
            ('projects', 'project_id')
        ],
        'referenced_by': []
    },
    'materials': {
        'references': [],
        'referenced_by': [('project_materials', 'material_id')]
    },
    'project_stages': {
        'references': [
            ('projects', 'project_id'),
            ('contractors', 'contractor_id')
        ],
        'referenced_by': []
    },
    'project_materials': {
        'references': [
            ('projects', 'project_id'),
            ('materials', 'material_id'),
            ('suppliers', 'supplier_id')
        ],
        'referenced_by': []
    },
    'partner_group_members': {
        'references': [
            ('partner_groups', 'group_id'),
            ('partners', 'partner_id')
        ],
        'referenced_by': []
    },
    'unit_partners': {
        'references': [
            ('units', 'unit_id'),
            ('partners', 'partner_id')
        ],
        'referenced_by': []
    },
    'partner_debts': {
        'references': [
            ('partners', 'creditor_id'),
            ('partners', 'debtor_id'),
            ('units', 'unit_id')
        ],
        'referenced_by': []
    },
    'broker_dues': {
        'references': [('brokers', 'broker_id')],
        'referenced_by': []
    },
    'safe_transfers': {
        'references': [
            ('safes', 'from_safe_id'),
            ('safes', 'to_safe_id')
        ],
        'referenced_by': []
    },
    'audit_logs': {
        'references': [],
        'referenced_by': []
    }
}

# Generate migration script
def generate_migration():
    migration = '''"""Convert all string IDs to integer IDs with autoincrement

Revision ID: convert_string_to_int_ids
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'convert_string_to_int_ids'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Create temporary ID mapping tables
'''
    
    # Add temporary mapping tables
    for table in TABLES:
        migration += f'''    op.create_table(
        '{table}_id_map',
        sa.Column('old_id', sa.String(20), primary_key=True),
        sa.Column('new_id', sa.Integer, primary_key=True, autoincrement=True)
    )
    
'''
    
    # Step 2: Copy data to mapping tables
    migration += '''    # Step 2: Populate mapping tables with existing IDs
    connection = op.get_bind()
    
'''
    
    for table in TABLES:
        migration += f'''    # Copy {table} IDs
    result = connection.execute(sa.text("SELECT id FROM {table} ORDER BY created_at"))
    for row in result:
        connection.execute(sa.text(
            "INSERT INTO {table}_id_map (old_id) VALUES (:old_id)"
        ), {{"old_id": row.id}})
    
'''
    
    # Step 3: Add new integer columns
    migration += '''    # Step 3: Add new integer ID columns
'''
    
    for table in TABLES:
        migration += f'''    op.add_column('{table}', sa.Column('new_id', sa.Integer))
'''
    
    # Step 4: Update new IDs from mapping
    migration += '''
    # Step 4: Update new IDs from mapping tables
'''
    
    for table in TABLES:
        migration += f'''    connection.execute(sa.text(
        "UPDATE {table} SET new_id = (SELECT new_id FROM {table}_id_map WHERE old_id = {table}.id)"
    ))
'''
    
    # Step 5: Update foreign keys
    migration += '''
    # Step 5: Update all foreign key references
'''
    
    for table, config in TABLES.items():
        for ref_table, ref_column in config['referenced_by']:
            # Handle special case for entity_id in vouchers
            if ref_column == 'entity_id' and ref_table == 'vouchers':
                migration += f'''    # Update vouchers.entity_id for {table}
    connection.execute(sa.text(
        "UPDATE vouchers SET entity_id = CAST((SELECT new_id FROM {table}_id_map WHERE old_id = vouchers.entity_id) AS VARCHAR) "
        "WHERE entity_type = '{table[:-1]}'"
    ))
'''
            else:
                migration += f'''    # Update {ref_table}.{ref_column}
    op.add_column('{ref_table}', sa.Column('new_{ref_column}', sa.Integer))
    connection.execute(sa.text(
        "UPDATE {ref_table} SET new_{ref_column} = (SELECT new_id FROM {table}_id_map WHERE old_id = {ref_table}.{ref_column})"
    ))
'''
    
    # Step 6: Drop old columns and rename new ones
    migration += '''
    # Step 6: Drop old columns and rename new ones
'''
    
    # First drop all foreign key constraints
    for table, config in TABLES.items():
        for ref_table, ref_column in config['references']:
            if ref_column != 'entity_id':  # Skip entity_id as it's polymorphic
                migration += f'''    op.drop_constraint('{ref_table}_{ref_column}_fkey', '{table}', type_='foreignkey')
'''
    
    # Drop old columns and rename new ones
    for table in TABLES:
        migration += f'''
    # Process {table}
    op.drop_column('{table}', 'id')
    op.alter_column('{table}', 'new_id', new_column_name='id')
    op.create_primary_key('{table}_pkey', '{table}', ['id'])
    op.alter_column('{table}', 'id', autoincrement=True)
'''
    
    # Update foreign key columns
    for table, config in TABLES.items():
        for ref_table, ref_column in config['referenced_by']:
            if ref_column != 'entity_id':  # Skip entity_id
                migration += f'''
    # Update {ref_table}.{ref_column}
    op.drop_column('{ref_table}', '{ref_column}')
    op.alter_column('{ref_table}', 'new_{ref_column}', new_column_name='{ref_column}')
'''
    
    # Step 7: Recreate foreign key constraints
    migration += '''
    # Step 7: Recreate all foreign key constraints
'''
    
    for table, config in TABLES.items():
        for ref_table, ref_column in config['references']:
            if ref_column != 'entity_id':
                migration += f'''    op.create_foreign_key('{table}_{ref_column}_fkey', '{table}', '{ref_table}', ['{ref_column}'], ['id'])
'''
    
    # Step 8: Drop mapping tables
    migration += '''
    # Step 8: Clean up - drop mapping tables
'''
    
    for table in TABLES:
        migration += f'''    op.drop_table('{table}_id_map')
'''
    
    migration += '''

def downgrade():
    # This migration is not reversible due to data dependencies
    raise NotImplementedError("Cannot downgrade from integer to string IDs")
'''
    
    return migration

if __name__ == '__main__':
    migration_content = generate_migration()
    
    # Create migrations directory if it doesn't exist
    os.makedirs('migrations/versions', exist_ok=True)
    
    # Write migration file
    with open('migrations/versions/convert_string_to_int_ids.py', 'w') as f:
        f.write(migration_content)
    
    print("Migration file created: migrations/versions/convert_string_to_int_ids.py")
    print("\nNext steps:")
    print("1. Review the generated migration file")
    print("2. Run: flask db upgrade")
    print("3. Update all model definitions to use Integer IDs")