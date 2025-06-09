from src import create_app
from src.database import db
from src.models.user import User

app = create_app()

with app.app_context():
    # Créer toutes les tables
    db.create_all()
    
    # Créer un utilisateur de test
    if not User.query.filter_by(username='admin').first():
        user = User(username='admin', email='admin@citrus.local')
        user.set_password('admin123')
        db.session.add(user)
        db.session.commit()
        print("Utilisateur admin créé avec succès !")
    else:
        print("L'utilisateur admin existe déjà.")
