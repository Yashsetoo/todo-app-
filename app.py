from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# Database config - uses SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, './todos.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

db = SQLAlchemy(app)

# ── Model ──────────────────────────────────────────────────
class Todo(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    description= db.Column(db.String(500), default='')
    priority   = db.Column(db.String(10), default='medium')   # low / medium / high
    completed  = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':          self.id,
            'title':       self.title,
            'description': self.description,
            'priority':    self.priority,
            'completed':   self.completed,
            'created_at':  self.created_at.strftime('%b %d, %Y')
        }

# ── Routes ─────────────────────────────────────────────────
@app.route('/')
def index():
    filter_by = request.args.get('filter', 'all')
    if filter_by == 'active':
        todos = Todo.query.filter_by(completed=False).order_by(Todo.created_at.desc()).all()
    elif filter_by == 'completed':
        todos = Todo.query.filter_by(completed=True).order_by(Todo.created_at.desc()).all()
    else:
        todos = Todo.query.order_by(Todo.created_at.desc()).all()

    total     = Todo.query.count()
    active    = Todo.query.filter_by(completed=False).count()
    completed = Todo.query.filter_by(completed=True).count()

    return render_template('index.html',
                           todos=todos,
                           filter_by=filter_by,
                           total=total,
                           active=active,
                           completed=completed)

@app.route('/add', methods=['POST'])
def add():
    title       = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    priority    = request.form.get('priority', 'medium')

    if title:
        todo = Todo(title=title, description=description, priority=priority)
        db.session.add(todo)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/toggle/<int:todo_id>', methods=['POST'])
def toggle(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    todo.completed = not todo.completed
    db.session.commit()
    return jsonify({'completed': todo.completed})

@app.route('/delete/<int:todo_id>', methods=['POST'])
def delete(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    db.session.delete(todo)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/edit/<int:todo_id>', methods=['POST'])
def edit(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    todo.title       = request.form.get('title', todo.title).strip()
    todo.description = request.form.get('description', todo.description).strip()
    todo.priority    = request.form.get('priority', todo.priority)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/clear-completed', methods=['POST'])
def clear_completed():
    Todo.query.filter_by(completed=True).delete()
    db.session.commit()
    return redirect(url_for('index'))

# ── Init ───────────────────────────────────────────────────
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=False)
