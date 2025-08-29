#!/usr/bin/env python3
"""Seed sample phase and partner data"""
from app import app, db
from acc.models import (Project, Phase, PhasePartnerGroup, PhasePartner, 
                       Partner, Expense, MaterialIssue, Material)
from acc.services.utils import generate_uid
from datetime import datetime, timedelta

with app.app_context():
    print("Seeding phase and partner data...")
    
    # Get or create a project
    project = Project.query.first()
    if not project:
        project = Project(
            id=generate_uid('PRJ'),
            name='مشروع برج النيل',
            code='NILE-001',
            project_type='عقاري',
            budget=10000000,
            status='نشط'
        )
        db.session.add(project)
        db.session.commit()
        print(f"Created project: {project.name}")
    
    # Create partners if they don't exist
    partner_names = ['أحمد محمد', 'محمود علي', 'خالد حسن', 'سعيد أحمد']
    partners = []
    
    for name in partner_names:
        partner = Partner.query.filter_by(name=name).first()
        if not partner:
            partner = Partner(
                id=generate_uid('P'),
                name=name,
                phone=f'0100000000{len(partners)}',
                national_id=f'2900101010101{len(partners)}'
            )
            db.session.add(partner)
            partners.append(partner)
        else:
            partners.append(partner)
    
    db.session.commit()
    print(f"Created/found {len(partners)} partners")
    
    # Create phases
    phases_data = [
        {
            'name': 'مرحلة الأساسات',
            'description': 'حفر وصب الأساسات الخرسانية',
            'groups': [
                {'name': 'المجموعة الرئيسية', 'percentage': 60, 'partners': [0, 1]},
                {'name': 'المستثمرون', 'percentage': 40, 'partners': [2, 3]}
            ]
        },
        {
            'name': 'مرحلة الهيكل الخرساني',
            'description': 'بناء الأعمدة والأسقف الخرسانية',
            'groups': [
                {'name': 'الملاك', 'percentage': 70, 'partners': [0, 2]},
                {'name': 'الشركاء', 'percentage': 30, 'partners': [1, 3]}
            ]
        }
    ]
    
    for idx, phase_data in enumerate(phases_data):
        # Create phase
        phase = Phase(
            id=generate_uid('PH'),
            project_id=project.id,
            name=phase_data['name'],
            description=phase_data['description'],
            start_date=datetime.now() + timedelta(days=idx*30),
            end_date=datetime.now() + timedelta(days=(idx+1)*30)
        )
        db.session.add(phase)
        db.session.commit()
        print(f"\nCreated phase: {phase.name}")
        
        # Create groups and add partners
        for group_data in phase_data['groups']:
            group = PhasePartnerGroup(
                id=generate_uid('PPG'),
                phase_id=phase.id,
                name=group_data['name'],
                share_percentage=group_data['percentage']
            )
            db.session.add(group)
            db.session.commit()
            print(f"  Created group: {group.name} ({group.share_percentage}%)")
            
            # Add partners to group
            partner_share = 100 / len(group_data['partners'])  # Equal shares
            for partner_idx in group_data['partners']:
                phase_partner = PhasePartner(
                    id=generate_uid('PP'),
                    group_id=group.id,
                    partner_id=partners[partner_idx].id,
                    share_percentage=partner_share
                )
                db.session.add(phase_partner)
                print(f"    Added partner: {partners[partner_idx].name} ({partner_share}%)")
            
            db.session.commit()
        
        # Add some sample expenses
        for i in range(3):
            expense = Expense(
                id=generate_uid('EXP'),
                phase_id=phase.id,
                paid_by_partner_id=partners[i % len(partners)].id,
                amount=50000 + (i * 10000),
                category='مواد بناء' if i % 2 == 0 else 'أجور عمال',
                description=f'مصروف رقم {i+1}',
                expense_date=datetime.now()
            )
            db.session.add(expense)
        
        db.session.commit()
        print(f"  Added sample expenses for phase")
    
    # Create some materials
    materials_data = [
        {'name': 'أسمنت', 'unit': 'شيكارة', 'unit_cost': 100},
        {'name': 'حديد', 'unit': 'طن', 'unit_cost': 20000},
        {'name': 'رمل', 'unit': 'متر مكعب', 'unit_cost': 150}
    ]
    
    for mat_data in materials_data:
        material = Material.query.filter_by(name=mat_data['name']).first()
        if not material:
            material = Material(
                id=generate_uid('M'),
                name=mat_data['name'],
                unit=mat_data['unit'],
                unit_cost=mat_data['unit_cost']
            )
            db.session.add(material)
    
    db.session.commit()
    print("\nSeeding completed successfully!")