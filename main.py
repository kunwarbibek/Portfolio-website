from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SECRET_KEY'] = 'shadoow'

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    github_url = db.Column(db.String(255), nullable=True)  
    image = db.Column(db.String(255), nullable=True)       
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()



@app.route('/')
def home():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('index.html', projects=projects)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user:
            flash("Username already exists!", "danger")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        # pyrefly: ignore [unexpected-keyword]
        new_user = User(username=username, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        flash("Registration Successful!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user'] = user.username
            flash("Login Successful!", "success")
            return redirect(url_for('home'))

        flash("Invalid Username or Password", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged Out Successfully!", "info")
    return redirect(url_for('home'))


@app.route('/project/add', methods=['POST'])
def add_project():
    if 'user' not in session:
        flash("Please log in to perform this action.", "danger")
        return redirect(url_for('login'))

    title = request.form.get('title')
    description = request.form.get('description')
    github_url = request.form.get('github_url')
    image = request.form.get('image')

    if not title or not description:
        flash("Title and description are required!", "danger")
        return redirect(url_for('home'))

    project = Project(
        # pyrefly: ignore [unexpected-keyword]
        title=title,
        # pyrefly: ignore [unexpected-keyword]
        description=description,
        # pyrefly: ignore [unexpected-keyword]
        github_url=github_url,
        # pyrefly: ignore [unexpected-keyword]
        image=image
    )

    db.session.add(project)
    db.session.commit()

    flash("Project Added Successfully!", "success")
    return redirect(url_for('home'))


@app.route('/project/update/<int:id>', methods=['POST'])
def update_project(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    project = Project.query.get_or_404(id)

    project.title = request.form.get('title')
    project.description = request.form.get('description')
    project.url = request.form.get('url')
    project.github_url = request.form.get('github_url')
    project.image = request.form.get('image')

    db.session.commit()

    flash("Project Updated Successfully!", "success")
    return redirect(url_for('home'))


@app.route('/project/delete/<int:id>')
def delete_project(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    project = Project.query.get_or_404(id)

    db.session.delete(project)
    db.session.commit()

    flash("Project Deleted!", "success")
    return redirect(url_for('home'))



@app.route('/project/<int:id>')
def project_detail(id):
    project = Project.query.get_or_404(id)
    return render_template('project.html', project=project)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('dashboard.html', projects=projects)   



if __name__ == "__main__":
    app.run(debug=True)