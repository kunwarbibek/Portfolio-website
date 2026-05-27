from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SECRET_KEY'] = 'shadoow'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# ==========================
# MODELS
# ==========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    github_url = db.Column(db.String(255))
    image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()

# ==========================
# HOME
# ==========================

@app.route('/')
def home():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    blogs = Blog.query.order_by(Blog.created_at.desc()).all()
    return render_template('index.html', projects=projects, blogs=blogs)

# ==========================
# REGISTER
# ==========================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "danger")
            return redirect(url_for('register'))

        user = User(
            # pyrefly: ignore [unexpected-keyword]
            username=username,
            # pyrefly: ignore [unexpected-keyword]
            password=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration Successful!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# ==========================
# LOGIN
# ==========================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user'] = user.username
            flash("Login Successful!", "success")
            return redirect(url_for('dashboard'))

        flash("Invalid Username or Password", "danger")

    return render_template('login.html')

# ==========================
# LOGOUT
# ==========================

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged Out Successfully!", "success")
    return redirect(url_for('home'))

# ==========================
# DASHBOARD
# ==========================

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    projects = Project.query.order_by(Project.created_at.desc()).all()
    blogs = Blog.query.order_by(Blog.created_at.desc()).all()

    return render_template('dashboard.html', projects=projects, blogs=blogs)

# ==========================
# ADD PROJECT
# ==========================

@app.route('/project/add', methods=['POST'])
def add_project():
    if 'user' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('login'))

    title = request.form.get('title')
    description = request.form.get('description')
    github_url = request.form.get('github_url')

    if not title or not description:
        flash("Title and description are required.", "danger")
        return redirect(url_for('dashboard'))

    image_path = None

    uploaded_file = request.files.get('image')

    if uploaded_file and uploaded_file.filename:

        filename = (
            f"{int(datetime.utcnow().timestamp())}_"
            f"{secure_filename(uploaded_file.filename)}"
        )

        filepath = os.path.join(
            app.config['UPLOAD_FOLDER'],
            filename
        )

        uploaded_file.save(filepath)

        image_path = f"uploads/{filename}"

    project = Project(
        # pyrefly: ignore [unexpected-keyword]
        title=title,
        # pyrefly: ignore [unexpected-keyword]
        description=description,
        # pyrefly: ignore [unexpected-keyword]
        github_url=github_url,
        # pyrefly: ignore [unexpected-keyword]
        image=image_path
    )

    db.session.add(project)
    db.session.commit()

    flash("Project Added Successfully!", "success")

    return redirect(url_for('dashboard'))


# ==========================
# UPDATE PROJECT
# ==========================

@app.route('/project/update/<int:id>', methods=['POST'])
def update_project(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    project = Project.query.get_or_404(id)

    project.title = request.form.get('title')
    project.description = request.form.get('description')
    project.github_url = request.form.get('github_url')

    uploaded_file = request.files.get('image')

    if uploaded_file and uploaded_file.filename:

        filename = (
            f"{int(datetime.utcnow().timestamp())}_"
            f"{secure_filename(uploaded_file.filename)}"
        )

        filepath = os.path.join(
            app.config['UPLOAD_FOLDER'],
            filename
        )

        uploaded_file.save(filepath)

        project.image = f"uploads/{filename}"

    db.session.commit()

    flash("Project Updated Successfully!", "success")

    return redirect(url_for('dashboard'))


# ==========================
# DELETE PROJECT
# ==========================

@app.route('/project/delete/<int:id>')
def delete_project(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    project = Project.query.get_or_404(id)

    # delete image file
    if project.image:
        image_path = os.path.join(
            'static',
            project.image
        )

        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(project)
    db.session.commit()

    flash("Project Deleted Successfully!", "success")

    return redirect(url_for('dashboard'))


# ==========================
# PROJECT DETAILS
# ==========================

@app.route('/project/<int:id>')
def project_detail(id):
    project = Project.query.get_or_404(id)

    return render_template(
        'project.html',
        project=project
    )


# ==========================
# BLOG ADD (FIXED)
# ==========================

@app.route('/blog/add', methods=['POST'])
def add_blog():
    if 'user' not in session:
        return redirect(url_for('login'))

    title = request.form.get('title')
    description = request.form.get('description')

    if not title or not description:
        flash("Title and description required!", "danger")
        return redirect(url_for('home'))

    file = request.files.get('image')
    image_path = None

    if file and file.filename:
        filename = f"{int(datetime.utcnow().timestamp())}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        image_path = f"uploads/{filename}"

    blog = Blog(
        # pyrefly: ignore [unexpected-keyword]
        title=title,
        # pyrefly: ignore [unexpected-keyword]
        description=description,
        # pyrefly: ignore [unexpected-keyword]
        image=image_path
    )

    db.session.add(blog)
    db.session.commit()

    flash("Blog Added!", "success")
    return redirect(url_for('home'))

# ==========================
# BLOG UPDATE (FIXED)
# ==========================

@app.route('/blog/update/<int:id>', methods=['POST'])
def update_blog(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    blog = Blog.query.get_or_404(id)

    blog.title = request.form.get('title')
    blog.description = request.form.get('description')

    db.session.commit()

    flash("Blog Updated!", "success")
    return redirect(url_for('home'))

# ==========================
# BLOG DELETE (FIXED)
# ==========================

@app.route('/blog/delete/<int:id>')
def delete_blog(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    blog = Blog.query.get_or_404(id)

    if blog.image:
        path = os.path.join('static', blog.image)
        if os.path.exists(path):
            os.remove(path)

    db.session.delete(blog)
    db.session.commit()

    flash("Blog Deleted!", "success")
    return redirect(url_for('dashboard'))

# ==========================
# BLOG DETAIL
# ==========================

@app.route('/blog/<int:id>')
def blog_detail(id):
    blog = Blog.query.get_or_404(id)
    return render_template('blog.html', blog=blog)



# ==========================
# RUN
# ==========================

if __name__ == "__main__":
    app.run(debug=True)