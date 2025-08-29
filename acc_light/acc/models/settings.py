from acc.extensions import db
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, func


class Settings(db.Model):
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True)
    
    # معلومات الشركة
    company_name = Column(String(200))
    company_address = Column(Text)
    company_phone = Column(String(50))
    company_email = Column(String(100))
    tax_number = Column(String(50))
    commercial_register = Column(String(50))
    
    # إعدادات العملة
    currency_symbol = Column(String(10), default='ج.م')
    currency_position = Column(String(10), default='after')  # before/after
    
    # إعدادات النظام
    fiscal_year_start = Column(String(5), default='01-01')  # MM-DD
    default_payment_terms = Column(Integer, default=30)  # days
    invoice_prefix = Column(String(10), default='INV-')
    contract_prefix = Column(String(10), default='CT-')
    
    # إعدادات الإشعارات
    enable_email_notifications = Column(Boolean, default=False)
    notification_email = Column(String(100))
    
    # إعدادات النسخ الاحتياطي
    auto_backup_enabled = Column(Boolean, default=False)
    backup_frequency = Column(String(20), default='daily')  # daily/weekly/monthly
    backup_retention_days = Column(Integer, default=30)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f'<Settings {self.company_name}>'
    
    @staticmethod
    def get_instance():
        """Get or create settings instance"""
        settings = Settings.query.first()
        if not settings:
            settings = Settings()
            db.session.add(settings)
            db.session.commit()
        return settings