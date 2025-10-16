# --- 1. IMPORTS & INITIALIZATION ---
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_flatpages import FlatPages
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import uuid

# --- 2. APP CONFIGURATION ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.secret_key = 'CHANGE_THIS_IN_PRODUCTION' # NOTE: Remember to change this
app.jinja_env.globals['title'] = 'NEMO'

# FlatPages Configuration
app.config['FLATPAGES_EXTENSION'] = '.md'
app.config['FLATPAGES_ROOT'] = 'posts'
app.config['FLATPAGES_AUTO_RELOAD'] = True

# --- 3. EXTENSIONS INITIALIZATION ---
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
pages = FlatPages(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- 4. DATABASE MODELS ---
# NOTE: The 'Post' model is likely obsolete (see section 7 below)
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    tags = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=False)
    desc = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime)
    image_path = db.Column(db.String(255))
    status = db.Column(db.String(20), nullable=False, default='published')
    post_type = db.Column(db.String(50), nullable=False, default='News')
    is_solved = db.Column(db.Boolean, default=False)
    solver_name = db.Column(db.String(100), nullable=True)
    solution_content = db.Column(db.Text, nullable=True)

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(128), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(128))
    is_authenticated = db.Column(db.Boolean, default=False)
    about_me = db.Column(db.Text, nullable=True)
    profile_image_path = db.Column(db.String(255), nullable=True, default='static/uploads/default_avatar.png')

    def __init__(self, email:str, password:str, name:str):
        self.email = email
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        self.name = name
        self.is_authenticated = False

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    def authenticate(self): self.is_authenticated = True
    def logout(self): self.is_authenticated = False

# --- 5. AUTHENTICATION & USER MANAGEMENT ---
@login_manager.user_loader
def user_loader(user_id):
    return db.session.get(User, user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and user.check_password(request.form['password']):
            user.authenticate()
            db.session.commit()
            login_user(user, remember=True)
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    current_user.logout()
    db.session.commit()
    logout_user()
    return redirect(url_for('index'))

@app.route('/account-settings', methods=['GET', 'POST'])
@login_required
def account_settings():
    if request.method == 'POST':
        if not current_user.check_password(request.form.get('current_password')):
            flash('Incorrect password. Please try again.', 'danger')
            return redirect(url_for('account_settings'))

        user = current_user
        new_email = request.form.get('email')
        if new_email != user.email and User.query.filter_by(email=new_email).first():
            flash('That email address is already in use.', 'danger')
            return redirect(url_for('account_settings'))

        user.email = new_email
        user.name = request.form.get('name')
        user.about_me = request.form.get('about_me')
        
        new_password = request.form.get('password')
        if new_password:
            user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            
        if 'profile_pic' in request.files:
            profile_pic = request.files['profile_pic']
            if profile_pic.filename != '':
                filename = secure_filename(profile_pic.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                profile_pic.save(image_path)
                user.profile_image_path = image_path

        db.session.commit()
        flash('Your settings have been updated successfully!', 'success')
        return redirect(url_for('account_settings'))
    return render_template('account-settings.html', logado=current_user.is_authenticated)

# --- 6. MAIN PAGE ROUTES ---
@app.route('/')
def index():
    published_pages = [p for p in pages if p.meta.get('status') == 'published']
    sorted_pages = sorted(published_pages, key=lambda p: p.meta.get('date', datetime.now()), reverse=True)
    news_posts = [p for p in sorted_pages if p.path.startswith('news/')]
    problem_post = next((p for p in sorted_pages if p.path.startswith('months-problems/') and not p.meta.get('is_solved')), None)
    return render_template('index.html', logado=current_user.is_authenticated, news_posts=news_posts, problem_post=problem_post)

@app.route('/about')
def about(): return render_template('about.html', logado=current_user.is_authenticated)

@app.route('/materials')
def materials(): return render_template('materials.html', logado=current_user.is_authenticated)

@app.route('/months-problems')
def months_problems():
    # Fetch all published "Month-Problem" posts from the file system
    problem_pages = [p for p in pages if p.meta.get('status') == 'published' and p.path.startswith('months-problems/') and p.meta.get('post_type') == 'Month-Problem']
    # Sort by 'is_solved' (False comes first), then by date (newest first)
    sorted_problems = sorted(problem_pages, key=lambda p: (p.meta.get('is_solved', False), p.meta['date']), reverse=False)
    return render_template('months-problems.html', logado=current_user.is_authenticated, post_list=sorted_problems)

@app.route('/news')
def news():
    news_pages = [p for p in pages if p.meta.get('status') == 'published' and p.path.startswith('news/')]
    sorted_news = sorted(news_pages, key=lambda p: p.meta.get('date', datetime.now()), reverse=True)
    award_posts = [p for p in sorted_news if p.path.startswith('news/awards/')]
    other_news_posts = [p for p in sorted_news if p.path.startswith('news/others/')]
    return render_template('news.html', logado=current_user.is_authenticated, award_posts=award_posts, other_news_posts=other_news_posts)

@app.route('/team')
def team(): return render_template('team.html', logado=current_user.is_authenticated)

@app.route('/faq')
def faq(): return render_template('faq.html', logado=current_user.is_authenticated)

@app.route('/contact')
def contact(): return render_template('contact.html', logado=current_user.is_authenticated)

@app.route('/post/<path:path>')
def view_post(path):
    post = pages.get_or_404(path)
    author = None
    author_email = post.meta.get('author_email')
    if author_email:
        author = User.query.filter_by(email=author_email).first()
    return render_template('view-post-flat.html', post=post, author=author, logado=current_user.is_authenticated)

# --- 7. DATABASE-BACKED POST EDITOR (LIKELY OBSOLETE) ---
# The routes below are for a database-backed post editor. Since the site now uses
# Markdown files (FlatPages) for all content, this entire section may be obsolete
# and can likely be removed. It is kept here for now for safety.

@app.route('/post/new')
@app.route('/post/edit/<int:post_id>')
@login_required
def post_editor(post_id=None):
    post = db.session.get(Post, post_id) if post_id else None
    if post_id and not post:
        flash("Post not found!", "danger")
        return redirect(url_for('index'))
    return render_template('post-editor.html', post=post, logado=current_user.is_authenticated)

@app.route('/post/save', methods=['POST'], defaults={'post_id': None})
@app.route('/post/save/<int:post_id>', methods=['POST'])
@login_required
def save_post(post_id):
    post = db.session.get(Post, post_id) if post_id else Post()
    if post_id and not post: return "Post not found", 404
    post.status = 'draft' if 'save_draft' in request.form else 'published'
    post.title = request.form.get('post-title')
    post.desc = request.form.get('post-desc')
    post.content = request.form.get('post-content')
    post.tags = '|'.join([tag.strip() for tag in request.form.get('post-tags', '').splitlines() if tag.strip()]) or 'sem'
    image = request.files.get('image')
    if image and image.filename != '':
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
        post.image_path = image_path
    post.post_type = request.form.get('post_type')
    if post.post_type == 'Month-Problem':
        post.is_solved = 'is_solved' in request.form
        if post.is_solved:
            post.solver_name = request.form.get('solver_name')
            post.solution_content = request.form.get('solution_content')
        else:
            post.solver_name = None
            post.solution_content = None
    if not post_id: db.session.add(post)
    db.session.commit()
    flash('Post saved successfully!', 'success')
    return redirect(url_for('view_post', post_id=post.id))

@app.route('/delete-post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = db.session.get(Post, post_id)
    if post:
        if post.image_path and os.path.exists(post.image_path):
            os.remove(post.image_path)
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/drafts')
@login_required
def drafts():
    draft_posts = Post.query.filter_by(status='draft').order_by(Post.date.desc()).all()
    return render_template('drafts.html', post_list=draft_posts, len_post_list=len(draft_posts), logado=current_user.is_authenticated)

@app.route('/upload-image', methods=['POST'])
@login_required
def upload_image():
    file = request.files.get('file')
    if not file: return jsonify({'error': 'No file uploaded.'}), 400
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    url = url_for('static', filename=os.path.join('uploads', filename))
    return jsonify({'location': url})

# --- 8. MAIN EXECUTION ---
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
