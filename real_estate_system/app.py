from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///real_estate.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    property_type = db.Column(db.String(50), nullable=False)  # house, apartment, commercial
    bedrooms = db.Column(db.Integer, nullable=False)
    bathrooms = db.Column(db.Integer, nullable=False)
    area = db.Column(db.Float, nullable=False)  # in square meters
    location = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(300), nullable=False)
    status = db.Column(db.String(20), default='available')  # available, sold, rented
    images = db.Column(db.Text)  # JSON string of image URLs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    experience_years = db.Column(db.Integer, default=0)
    bio = db.Column(db.Text)
    profile_image = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    budget_min = db.Column(db.Float)
    budget_max = db.Column(db.Float)
    preferred_location = db.Column(db.String(200))
    property_type_preference = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, contacted, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def index():
    properties = Property.query.filter_by(status='available').limit(6).all()
    return render_template('index.html', properties=properties)

@app.route('/properties')
def properties():
    page = request.args.get('page', 1, type=int)
    property_type = request.args.get('type', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    query = Property.query.filter_by(status='available')
    
    if property_type:
        query = query.filter(Property.property_type == property_type)
    if min_price:
        query = query.filter(Property.price >= min_price)
    if max_price:
        query = query.filter(Property.price <= max_price)
    
    properties = query.paginate(page=page, per_page=12, error_out=False)
    return render_template('properties.html', properties=properties, 
                         property_type=property_type, min_price=min_price, max_price=max_price)

@app.route('/property/<int:property_id>')
def property_detail(property_id):
    property = Property.query.get_or_404(property_id)
    return render_template('property_detail.html', property=property)

@app.route('/agents')
def agents():
    agents = Agent.query.all()
    return render_template('agents.html', agents=agents)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']
        
        # Create client if doesn't exist
        client = Client.query.filter_by(email=email).first()
        if not client:
            client = Client(name=name, email=email, phone=phone)
            db.session.add(client)
            db.session.commit()
        
        flash('تم إرسال رسالتك بنجاح! سنتواصل معك قريباً.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/inquiry/<int:property_id>', methods=['POST'])
def submit_inquiry(property_id):
    property = Property.query.get_or_404(property_id)
    
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    message = request.form['message']
    
    # Create client if doesn't exist
    client = Client.query.filter_by(email=email).first()
    if not client:
        client = Client(name=name, email=email, phone=phone)
        db.session.add(client)
        db.session.commit()
    
    # Create inquiry
    inquiry = Inquiry(client_id=client.id, property_id=property_id, message=message)
    db.session.add(inquiry)
    db.session.commit()
    
    flash('تم إرسال استفسارك بنجاح!', 'success')
    return redirect(url_for('property_detail', property_id=property_id))

# Admin routes
@app.route('/admin')
def admin():
    properties_count = Property.query.count()
    agents_count = Agent.query.count()
    clients_count = Client.query.count()
    inquiries_count = Inquiry.query.count()
    
    return render_template('admin/dashboard.html', 
                         properties_count=properties_count,
                         agents_count=agents_count,
                         clients_count=clients_count,
                         inquiries_count=inquiries_count)

@app.route('/admin/properties')
def admin_properties():
    properties = Property.query.all()
    return render_template('admin/properties.html', properties=properties)

@app.route('/admin/add_property', methods=['GET', 'POST'])
def add_property():
    if request.method == 'POST':
        property = Property(
            title=request.form['title'],
            description=request.form['description'],
            price=float(request.form['price']),
            property_type=request.form['property_type'],
            bedrooms=int(request.form['bedrooms']),
            bathrooms=int(request.form['bathrooms']),
            area=float(request.form['area']),
            location=request.form['location'],
            address=request.form['address']
        )
        db.session.add(property)
        db.session.commit()
        flash('تم إضافة العقار بنجاح!', 'success')
        return redirect(url_for('admin_properties'))
    
    return render_template('admin/add_property.html')

@app.route('/admin/agents')
def admin_agents():
    agents = Agent.query.all()
    return render_template('admin/agents.html', agents=agents)

@app.route('/admin/add_agent', methods=['GET', 'POST'])
def add_agent():
    if request.method == 'POST':
        agent = Agent(
            name=request.form['name'],
            email=request.form['email'],
            phone=request.form['phone'],
            license_number=request.form['license_number'],
            experience_years=int(request.form['experience_years']),
            bio=request.form['bio']
        )
        db.session.add(agent)
        db.session.commit()
        flash('تم إضافة الوكيل بنجاح!', 'success')
        return redirect(url_for('admin_agents'))
    
    return render_template('admin/add_agent.html')

@app.route('/admin/inquiries')
def admin_inquiries():
    inquiries = Inquiry.query.join(Client).join(Property).all()
    return render_template('admin/inquiries.html', inquiries=inquiries)

# API routes
@app.route('/api/properties')
def api_properties():
    properties = Property.query.filter_by(status='available').all()
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'price': p.price,
        'property_type': p.property_type,
        'bedrooms': p.bedrooms,
        'bathrooms': p.bathrooms,
        'area': p.area,
        'location': p.location,
        'images': p.images
    } for p in properties])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Add sample data if database is empty
        if Property.query.count() == 0:
            sample_properties = [
                Property(
                    title='فيلا فاخرة في الرياض',
                    description='فيلا حديثة مع حديقة واسعة وحمام سباحة',
                    price=2500000,
                    property_type='house',
                    bedrooms=5,
                    bathrooms=4,
                    area=450,
                    location='الرياض',
                    address='حي النرجس، الرياض'
                ),
                Property(
                    title='شقة عصرية في جدة',
                    description='شقة مفروشة بالكامل مع إطلالة على البحر',
                    price=1200000,
                    property_type='apartment',
                    bedrooms=3,
                    bathrooms=2,
                    area=120,
                    location='جدة',
                    address='حي الزهراء، جدة'
                ),
                Property(
                    title='مكتب تجاري في الدمام',
                    description='مكتب في موقع مميز مع مواقف سيارات',
                    price=800000,
                    property_type='commercial',
                    bedrooms=0,
                    bathrooms=2,
                    area=200,
                    location='الدمام',
                    address='حي الفيصلية، الدمام'
                )
            ]
            
            for prop in sample_properties:
                db.session.add(prop)
            
            sample_agents = [
                Agent(
                    name='أحمد محمد',
                    email='ahmed@realestate.com',
                    phone='+966501234567',
                    license_number='RE123456',
                    experience_years=5,
                    bio='خبير في العقارات السكنية والتجارية'
                ),
                Agent(
                    name='فاطمة علي',
                    email='fatima@realestate.com',
                    phone='+966507654321',
                    license_number='RE789012',
                    experience_years=8,
                    bio='متخصصة في العقارات الفاخرة والاستثمارية'
                )
            ]
            
            for agent in sample_agents:
                db.session.add(agent)
            
            db.session.commit()
    
    app.run(debug=True, host='0.0.0.0', port=5000)