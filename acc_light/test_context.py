from app import app
from flask import render_template_string

test_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Test Context</title>
</head>
<body>
    <h1>Context Test</h1>
    <h2>All Projects Count: {{ all_projects|length if all_projects else 0 }}</h2>
    <h2>Current Project: {{ current_project.name if current_project else 'None' }}</h2>
    
    <h3>Projects List:</h3>
    <ul>
    {% for project in all_projects %}
        <li>{{ project.name }} ({{ project.code }})</li>
    {% else %}
        <li>No projects found!</li>
    {% endfor %}
    </ul>
    
    <h3>Debug Info:</h3>
    <p>all_projects is defined: {{ all_projects is defined }}</p>
    <p>all_projects is none: {{ all_projects is none }}</p>
    <p>all_projects type: {{ all_projects.__class__.__name__ if all_projects else 'None' }}</p>
</body>
</html>
'''

@app.route('/test-context')
def test_context():
    return render_template_string(test_template)

if __name__ == '__main__':
    with app.app_context():
        print("Testing context directly...")
        from acc.models import Project
        projects = Project.query.filter_by(status='نشط').order_by(Project.name).all()
        print(f"Found {len(projects)} active projects")
        
    app.run(host='0.0.0.0', port=5002, debug=True)