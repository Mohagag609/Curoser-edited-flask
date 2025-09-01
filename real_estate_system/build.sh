#!/bin/bash

echo "🏗️  Building Real Estate System..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create database
echo "🗄️  Setting up database..."
python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database created successfully!')
"

# Create static files directory structure
echo "📁 Creating static files structure..."
mkdir -p static/css static/js static/images

# Create a simple CSS file
cat > static/css/style.css << 'EOF'
/* Custom styles for Real Estate System */
.property-card {
    transition: all 0.3s ease;
}

.property-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

.hero-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.price-tag {
    background: linear-gradient(45deg, #ff6b6b, #ee5a24);
    color: white;
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: 600;
}

.btn-primary {
    background: linear-gradient(45deg, #667eea, #764ba2);
    border: none;
}

.btn-primary:hover {
    background: linear-gradient(45deg, #5a6fd8, #6a4190);
}
EOF

# Create a simple JavaScript file
cat > static/js/main.js << 'EOF'
// Main JavaScript for Real Estate System
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
});
EOF

echo "✅ Build completed successfully!"
echo ""
echo "🚀 To run the application:"
echo "   cd real_estate_system"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "🌐 The application will be available at: http://localhost:5000"
echo "📊 Admin panel: http://localhost:5000/admin"
echo ""
echo "📋 Features included:"
echo "   ✅ Property listing and search"
echo "   ✅ Agent management"
echo "   ✅ Client inquiries"
echo "   ✅ Admin dashboard"
echo "   ✅ Responsive Arabic UI"
echo "   ✅ SQLite database"