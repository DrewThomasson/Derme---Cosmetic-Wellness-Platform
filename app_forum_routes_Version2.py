from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models_forum import ForumPost, ForumComment, ContentReport
from yourapp import db

bp = Blueprint('forum', __name__, url_prefix='/forum')

@bp.route('/')
def index():
    page = int(request.args.get('page', 1))
    posts = ForumPost.query.order_by(ForumPost.created_at.desc()).limit(50).all()
    return render_template('forum/index.html', posts=posts)

@bp.route('/post', methods=['GET','POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form.get('title')
        body = request.form.get('body')
        anon = request.form.get('anonymous') == 'on'
        post = ForumPost(author_id=current_user.id, title=title, body=body, is_anonymous=anon)
        db.session.add(post); db.session.commit()
        return redirect(url_for('forum.index'))
    return render_template('forum/new_post.html')

@bp.route('/post/<int:post_id>')
def view_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    comments = ForumComment.query.filter_by(post_id=post.id).order_by(ForumComment.created_at.asc()).all()
    return render_template('forum/view_post.html', post=post, comments=comments)