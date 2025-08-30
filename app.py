from acc import create_app, db
from acc.models import *  # Import all models

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True, host='0.0.0.0', port=5000)