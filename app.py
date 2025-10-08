import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename

# App Initialization and Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.secret_key = 'CHANGE_THIS_IN_PRODUCTION_TO_A_RANDOM_SECRET_KEY'
app.jinja_env.globals['title'] = 'NEMO'

# Extensions Initialization
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    tags = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=False)
    desc = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    image_path = db.Column(db.String(255))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    email = db.Column(db.String(128), primary_key=True)
    password_hash = db.Column(db.String(128))
    is_authenticated = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(100), nullable=True)
    about_me = db.Column(db.Text, nullable=True)
    profile_image_path = db.Column(db.String(255), nullable=True, default='static/uploads/default_avatar.png')

    def __init__(self, email:str, password:str, name:str):
        self.email = email
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        self.name = name
        self.is_authenticated = False

    def get_id(self):
        return self.email

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def authenticate(self):
        self.is_authenticated = True

    def logout(self):
        self.is_authenticated = False

# Flask-Login User Loader
@login_manager.user_loader
def user_loader(user_id):
    return db.session.get(User, user_id)

# --- Main Routes ---
@app.route('/')
def index():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('index.html', logado=current_user.is_authenticated, post_list=posts, len_post_list=len(posts))

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
        # Get the current user object
        user = current_user
        
        # Update text fields from the form
        user.name = request.form.get('name')
        user.about_me = request.form.get('about_me')
        
        # Conditionally update the password if a new one was provided
        new_password = request.form.get('password')
        if new_password:
            user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            
        # Conditionally handle the profile picture upload
        if 'profile_pic' in request.files:
            profile_pic = request.files['profile_pic']
            if profile_pic.filename != '':
                filename = secure_filename(profile_pic.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                profile_pic.save(image_path)
                user.profile_image_path = image_path

        # Save all the changes to the database
        db.session.commit()
        
        flash('Your settings have been updated successfully!', 'success')
        return redirect(url_for('account_settings'))

    # For a GET request, just show the page
    return render_template('account-settings.html', logado=current_user.is_authenticated)

# --- Post Routes ---
@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        return "Post not found", 404
    return render_template('view-post.html', post=post, logado=current_user.is_authenticated)

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
    if post_id and not post:
        return "Post not found", 404

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

    if not post_id:
        db.session.add(post)
    
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


@app.route('/about')
def about():
    return render_template('about.html', logado=current_user.is_authenticated)


@app.route('/faq')
def faq():
    return render_template('faq.html', logado=current_user.is_authenticated)


@app.route('/months-problems')
def months_problems():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('months-problems.html', logado=current_user.is_authenticated, post_list=posts, len_post_list=len(posts))


@app.route('/news')
def news():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template('news.html', logado=current_user.is_authenticated, post_list=posts, len_post_list=len(posts))


@app.route('/contact')
def contact():
    return render_template('contact.html', logado=current_user.is_authenticated)


@app.route('/materials')
def materials():
    return render_template('materials.html', logado=current_user.is_authenticated)

"""
@app.route('/create-post', methods=['GET'])
@login_required
def create_post_get():
    return render_template('create-post.html', logado=current_user.is_authenticated)


@app.route('/create-post', methods=['POST'])
@login_required
def create_post_post():
    # Obter os dados do formulário
    title = request.form.get('post-title')
    desc = request.form.get('post-desc')
    content = request.form.get('post-content')  # .replace('\r\n', '\n')
    tags = request.form.get('post-tags')
    image = request.files['image'] if 'image' in request.files else None

    # Processar as tags
    as_tags = tags.split('\r\n')
    as_tags = [a_tag for a_tag in as_tags if a_tag != '']
    if len(as_tags) == 0:
        as_tags.append('sem')
    as_tags = '|'.join(as_tags)

    # Salvar a imagem no servidor, se existir
    if image:
        filename = secure_filename(image.filename)
        base_filename, file_extension = os.path.splitext(filename)
        counter = 0
        while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
            counter += 1
            filename = f"{base_filename}_{counter}{file_extension}"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
    else:
        image_path = None

    # Criar o novo post
    new_post = Post(title=title, content=content,
                    tags=as_tags, image_path=image_path, desc=desc)
    db.session.add(new_post)
    db.session.commit()

    return jsonify({'success': True, 'post_id': new_post.id})


@app.route('/edit-post/<post_id>', methods=['GET'])
@login_required
def edit_post_get(post_id):
    post = db.session.get(Post, post_id)
    post_data = {'pid': post.id, 'ptitle': post.title,
                 'pcontent': post.content, 'ptags': post.tags, 'pimg_path': post.image_path,
                 'pdate': post.date, 'pdesc': post.desc}
    return render_template('edit-post.html', logado=current_user.is_authenticated, **post_data)


@app.route('/edit-post/<post_id>', methods=['POST'])
@login_required
def edit_post_post(post_id):
    # Obter os dados do formulário
    post = db.session.get(Post, post_id)
    title = request.form.get('post-title')
    desc = request.form.get('post-desc')
    content = request.form.get('post-content')  # .replace('\r\n', '\n')
    tags = request.form.get('post-tags')
    image = request.files['image'] if 'image' in request.files else None

    # Processar as tags
    as_tags = tags.split('\n')
    as_tags = [a_tag for a_tag in as_tags if a_tag != '']
    if len(as_tags) == 0:
        as_tags.append('sem')
    as_tags = '|'.join(as_tags)

    post.title = title
    post.desc = desc
    post.content = content
    post.tags = as_tags

    # Salvar a imagem no servidor, se existir
    if image:
        filename = secure_filename(image.filename)
        base_filename, file_extension = os.path.splitext(filename)
        counter = 0
        while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
            counter += 1
            filename = f"{base_filename}_{counter}{file_extension}"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
        if post.image_path is not None:
            os.remove(post.image_path)
        post.image_path = image_path
    else:
        image_path = None

    # Criar o novo post
    db.session.commit()

    return jsonify({'success': True, 'post_id': post_id})
"""

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    #with app.app_context():
    #    db.create_all()
    app.run(host='localhost', port=5000)
