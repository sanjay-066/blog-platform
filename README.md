# 📝 Blog Platform

A full-stack blogging platform built with **Flask + SQLite + Vanilla JS**. Features user authentication, post management, and a comment system.

## 🚀 Features

| Feature | Details |
|---------|---------|
| 🔐 **Auth** | Register, login with username/email, bcrypt password hashing, session persistence |
| ✍️ **Posts** | Create, edit, delete blog posts with live preview |
| 💬 **Comments** | Add/delete comments with real-time updates |
| 🔍 **Search** | Full-text search across post titles and content |
| 📄 **Pagination** | Server-side pagination (8 posts per page) |
| 🛡️ **Authorization** | Owners-only edit/delete via API + UI |
| 📱 **Responsive** | Mobile-friendly CSS with custom properties |

## 🏗️ Tech Stack

- **Backend**: Python 3.13 + Flask 3.1
- **Database**: SQLite via Flask-SQLAlchemy
- **Auth**: Flask-Login + Flask-Bcrypt
- **Frontend**: Vanilla JS (Fetch API) + HTML5 + CSS3
- **API**: RESTful JSON endpoints

## 📁 Project Structure

```
blog-platform/
├── app.py              # Flask app, models, all API routes
├── requirements.txt    # Python dependencies
├── instance/
│   └── blog.db         # SQLite database (auto-created)
├── templates/
│   ├── index.html      # Home page (post feed + search)
│   ├── login.html      # Login form
│   ├── register.html   # Registration form
│   ├── post_detail.html# Post view + comment section
│   ├── create_post.html# New post editor
│   ├── edit_post.html  # Edit post editor
│   ├── 404.html        # Not found page
│   └── 403.html        # Forbidden page
└── static/
    ├── css/style.css   # All styles (CSS custom properties)
    └── js/app.js       # Shared utilities + API client
```

## ⚡ Quick Start

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the server
python app.py

# 3. Open in browser
# http://127.0.0.1:5000
```

## 🔌 REST API Reference

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/me` | Get current user info |
| `POST` | `/api/register` | Create account `{username, email, password}` |
| `POST` | `/api/login` | Login `{identifier, password, remember?}` |
| `POST` | `/api/logout` | Logout |

### Posts
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/posts?page=1&per_page=8&search=...` | List posts (paginated) |
| `POST` | `/api/posts` | Create post `{title, body}` 🔒 |
| `GET` | `/api/posts/:id` | Get post + comments |
| `PUT` | `/api/posts/:id` | Edit post `{title, body}` 🔒 |
| `DELETE` | `/api/posts/:id` | Delete post 🔒 |

### Comments
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/posts/:id/comments` | List post comments |
| `POST` | `/api/posts/:id/comments` | Add comment `{body}` 🔒 |
| `DELETE` | `/api/comments/:id` | Delete comment 🔒 |

> 🔒 = Requires authentication
