"""
Blog Platform - Main Application
Flask backend with SQLite, user auth, posts, and comments.
"""
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

# ── App Setup ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod-2024!")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"


# ── Models ─────────────────────────────────────────────────────────────────────
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship("Post", backref="author", lazy=True, cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="author", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"id": self.id, "username": self.username, "email": self.email,
                "created_at": self.created_at.isoformat()}


class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.String(300))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    comments = db.relationship("Comment", backref="post", lazy=True, cascade="all, delete-orphan")

    def to_dict(self, include_comments=False):
        data = {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "excerpt": self.excerpt or self.body[:200],
            "author": self.author.username,
            "author_id": self.user_id,
            "comment_count": len(self.comments),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_comments:
            data["comments"] = [c.to_dict() for c in sorted(self.comments, key=lambda c: c.created_at)]
        return data


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "body": self.body,
            "author": self.author.username,
            "author_id": self.user_id,
            "post_id": self.post_id,
            "created_at": self.created_at.isoformat(),
        }


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ── Page Routes ────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/register")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/post/<int:post_id>")
def post_detail(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        abort(404)
    return render_template("post_detail.html", post_id=post_id)


@app.route("/create")
@login_required
def create_post_page():
    return render_template("create_post.html")


@app.route("/edit/<int:post_id>")
@login_required
def edit_post_page(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        abort(404)
    if post.user_id != current_user.id:
        abort(403)
    return render_template("edit_post.html", post_id=post_id)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


# ── RESTful API ────────────────────────────────────────────────────────────────

# Auth endpoints
@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400
    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify({"message": "Account created successfully!", "user": user.to_dict()}), 201


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    identifier = data.get("identifier", "").strip()
    password = data.get("password", "")

    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier.lower())
    ).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid username/email or password"}), 401

    login_user(user, remember=data.get("remember", False))
    return jsonify({"message": "Logged in successfully!", "user": user.to_dict()}), 200


@app.route("/api/logout", methods=["POST"])
@login_required
def api_logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200


@app.route("/api/me")
def api_me():
    if current_user.is_authenticated:
        return jsonify({"authenticated": True, "user": current_user.to_dict()})
    return jsonify({"authenticated": False}), 200


# Posts endpoints
@app.route("/api/posts", methods=["GET"])
def api_get_posts():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    search = request.args.get("search", "").strip()

    query = Post.query
    if search:
        query = query.filter(
            Post.title.ilike(f"%{search}%") | Post.body.ilike(f"%{search}%")
        )

    pagination = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        "posts": [p.to_dict() for p in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    })


@app.route("/api/posts", methods=["POST"])
@login_required
def api_create_post():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    title = data.get("title", "").strip()
    body = data.get("body", "").strip()

    if not title or not body:
        return jsonify({"error": "Title and body are required"}), 400
    if len(title) > 200:
        return jsonify({"error": "Title too long (max 200 chars)"}), 400

    excerpt = body[:200] + ("..." if len(body) > 200 else "")
    post = Post(title=title, body=body, excerpt=excerpt, user_id=current_user.id)
    db.session.add(post)
    db.session.commit()
    return jsonify({"message": "Post created!", "post": post.to_dict()}), 201


@app.route("/api/posts/<int:post_id>", methods=["GET"])
def api_get_post(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    return jsonify(post.to_dict(include_comments=True))


@app.route("/api/posts/<int:post_id>", methods=["PUT"])
@login_required
def api_update_post(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    if post.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    title = data.get("title", "").strip()
    body = data.get("body", "").strip()

    if not title or not body:
        return jsonify({"error": "Title and body are required"}), 400

    post.title = title
    post.body = body
    post.excerpt = body[:200] + ("..." if len(body) > 200 else "")
    post.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Post updated!", "post": post.to_dict()})


@app.route("/api/posts/<int:post_id>", methods=["DELETE"])
@login_required
def api_delete_post(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    if post.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    db.session.delete(post)
    db.session.commit()
    return jsonify({"message": "Post deleted successfully"})


# Comments endpoints
@app.route("/api/posts/<int:post_id>/comments", methods=["GET"])
def api_get_comments(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    comments = sorted(post.comments, key=lambda c: c.created_at)
    return jsonify({"comments": [c.to_dict() for c in comments], "count": len(comments)})


@app.route("/api/posts/<int:post_id>/comments", methods=["POST"])
@login_required
def api_create_comment(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    data = request.get_json()
    body = data.get("body", "").strip() if data else ""
    if not body:
        return jsonify({"error": "Comment body is required"}), 400
    if len(body) > 2000:
        return jsonify({"error": "Comment too long (max 2000 chars)"}), 400

    comment = Comment(body=body, user_id=current_user.id, post_id=post_id)
    db.session.add(comment)
    db.session.commit()
    return jsonify({"message": "Comment added!", "comment": comment.to_dict()}), 201


@app.route("/api/comments/<int:comment_id>", methods=["DELETE"])
@login_required
def api_delete_comment(comment_id):
    comment = db.session.get(Comment, comment_id)
    if not comment:
        return jsonify({"error": "Comment not found"}), 404
    if comment.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    db.session.delete(comment)
    db.session.commit()
    return jsonify({"message": "Comment deleted"})


# ── Error handlers ─────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403


# ── Init & Run ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("[OK] Database tables created.")
    app.run(debug=True, host="0.0.0.0", port=5000)
