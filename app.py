from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
import os

app = Flask(__name__)
CORS(app)

# Charger le fichier .env (assurez-vous qu'il est dans le même répertoire que votre script)
load_dotenv()

# Accéder à une variable :
POSTGRES_URL = os.getenv('DATABASE_URL')

app.config['SQLALCHEMY_DATABASE_URI'] = POSTGRES_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'JeanPierre'  # Secret pour JWT

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Modèle utilisateur pour l'authentification
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

class Evenement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lieu = db.Column(db.String)
    nom_evenement = db.Column(db.String)
    type = db.Column(db.String)
    artiste_id = db.Column(db.Integer, db.ForeignKey('artiste.id'))
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)
    photo = db.Column(db.String)
    descriptions = db.relationship('Description', backref='evenement', lazy=True)

class Description(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    evenement_id = db.Column(db.Integer, db.ForeignKey('evenement.id'))
    titre = db.Column(db.String)
    image = db.Column(db.String)
    date = db.Column(db.Date)
    ville = db.Column(db.String)
    description = db.Column(db.Text)

class Artiste(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String)
    genre_musical = db.Column(db.String)
    evenements = db.relationship('Evenement', backref='artiste', lazy=True)

@app.route('/')
def index():
    return "Hello, Supabase!"

# Route pour se connecter et obtenir un token
@app.route('/login', methods=['POST'])
def login():
    try:
        # Récupérer les données JSON envoyées par le client
        data = request.get_json()

        # Vérifier si les champs sont bien présents dans la requête
        if not data or 'name' not in data or 'password' not in data:
            return jsonify({'error': 'Missing name or password'}), 400
                
        # Chercher l'utilisateur en fonction du name (ou du champ `name` si c'est ce que tu utilises)
        user = User.query.filter_by(name=data['name']).first()

        # Si l'utilisateur n'existe pas ou si le mot de passe ne correspond pas
        if not user or not check_password_hash(user.password, data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401

        # Générer un token JWT si les informations d'identification sont correctes
        access_token = create_access_token(identity=user.name)

        # Retourner le token dans une réponse JSON
        return jsonify({'token': access_token}), 200

    except Exception as e:
        # Gérer toute erreur inattendue
        return jsonify({'error': str(e)}), 500


# Route sécurisée (exemple)
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({'message': f'Hello {current_user}!'}), 200

@app.route('/evenements', methods=['GET'])
def get_evenements():
    try:
        evenements = Evenement.query.all()
        evenements_json = []
        for evenement in evenements:
            artiste = Artiste.query.get(evenement.artiste_id)
            evenements_json.append({
                'id': evenement.id,
                'lieu': evenement.lieu,
                'nom_evenement': evenement.nom_evenement,
                'type': evenement.type,
                'artiste': {
                    'id': artiste.id,
                    'nom': artiste.nom,
                    'genre_musical': artiste.genre_musical
                },
                'longitude': evenement.longitude,
                'latitude': evenement.latitude,
                'photo': evenement.photo
            })
        return jsonify(evenements_json)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/evenements', methods=['POST'])
@jwt_required()  # Protection JWT
def add_evenement():
    try:
        data = request.get_json()
        evenement = Evenement(
            lieu=data['lieu'],
            nom_evenement=data['nom_evenement'],
            type=data['type'],
            artiste_id=data['artiste_id'],
            longitude=data['longitude'],
            latitude=data['latitude'],
            photo=data['photo']
        )
        db.session.add(evenement)
        db.session.commit()
        return jsonify({'message': 'Evenement added!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/evenements/<int:id>', methods=['GET'])
def get_evenement(id):
    try:
        evenement = Evenement.query.get(id)
        if evenement is None:
            return jsonify({'error': 'Evenement not found'}), 404
        artiste = Artiste.query.get(evenement.artiste_id)
        return jsonify({
            'id': evenement.id,
            'lieu': evenement.lieu,
            'nom_evenement': evenement.nom_evenement,
            'type': evenement.type,
            'artiste': {
                'id': artiste.id,
                'nom': artiste.nom,
                'genre_musical': artiste.genre_musical
            },
            'longitude': evenement.longitude,
            'latitude': evenement.latitude,
            'photo': evenement.photo
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/evenements/<int:id>', methods=['PUT'])
@jwt_required()  # Protection JWT
def update_evenement(id):
    try:
        evenement = Evenement.query.get(id)
        if evenement is None:
            return jsonify({'error': 'Evenement not found'}), 404
        data = request.get_json()
        evenement.lieu = data['lieu']
        evenement.nom_evenement = data['nom_evenement']
        evenement.type = data['type']
        evenement.artiste_id = data['artiste_id']
        evenement.longitude = data['longitude']
        evenement.latitude = data['latitude']
        evenement.photo = data['photo']
        db.session.commit()
        return jsonify({'message': 'Evenement updated!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/evenements/<int:id>', methods=['DELETE'])
@jwt_required()  # Protection JWT
def delete_evenement(id):
    try:
        evenement = Evenement.query.get(id)
        if evenement is None:
            return jsonify({'error': 'Evenement not found'}), 404
        db.session.delete(evenement)
        db.session.commit()
        return jsonify({'message': 'Evenement deleted!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/evenements/search', methods=['GET'])
def search_evenements():
    try:
        nom_artiste = request.form.get('nom_artiste')
        genre_musical = request.form.get('genre_musical')
        date = request.form.get('date')
        ville = request.form.get('ville')
        nom_evenement = request.form.get('nom_evenement')

        query = Evenement.query.join(Artiste).join(Description)

        if nom_artiste:
            query = query.filter(Artiste.nom.ilike(f'%{nom_artiste}%'))
        if genre_musical:
            query = query.filter(Artiste.genre_musical.ilike(f'%{genre_musical}%'))
        if date:
            query = query.filter(Description.date == date)
        if ville:
            query = query.filter(Description.ville.ilike(f'%{ville}%'))
        if nom_evenement:
            query = query.filter(Evenement.nom_evenement.ilike(f'%{nom_evenement}%'))

        evenements = query.all()

        evenements_json = [
            {
                'id': evenement.id,
                'lieu': evenement.lieu,
                'nom_evenement': evenement.nom_evenement,
                'type': evenement.type,
                'artiste_id': evenement.artiste_id,
                'longitude': evenement.longitude,
                'latitude': evenement.latitude,
                'photo': evenement.photo
            }
            for evenement in evenements
        ]

        return jsonify(evenements_json)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/descriptions', methods=['GET'])
def get_descriptions():
    try:
        descriptions = Description.query.all()
        descriptions_json = []
        for description in descriptions:
            descriptions_json.append({
                'id': description.id,
                'evenement_id': description.evenement_id,
                'titre': description.titre,
                'image': description.image,
                'date': description.date,
                'ville': description.ville,
                'description': description.description
            })
        return jsonify(descriptions_json)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/descriptions', methods=['POST'])
@jwt_required()  # Protection JWT
def add_description():
    try:
        data = request.get_json()
        description = Description(
            evenement_id=data['evenement_id'],
            titre=data['titre'],
            image=data['image'],
            date=data['date'],
            ville=data['ville'],
            description=data['description']
        )
        db.session.add(description)
        db.session.commit()
        return jsonify({'message': 'Description added!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/descriptions/<int:id>', methods=['GET'])
def get_description(id):
    try:
        description = Description.query.filter_by(evenement_id=id).first()
        if description is None:
            return jsonify({'error': 'Description not found'}), 404
        return jsonify({
            'id': description.id,
            'evenement_id': description.evenement_id,
            'titre': description.titre,
            'image': description.image,
            'date': description.date,
            'ville': description.ville,
            'description': description.description
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/descriptions/<int:id>', methods=['PUT'])
@jwt_required()  # Protection JWT
def update_description(id):
    try:
        description = Description.query.get(id)
        if description is None:
            return jsonify({'error': 'Description not found'}), 404
        data = request.get_json()
        description.evenement_id = data['evenement_id']
        description.titre = data['titre']
        description.image = data['image']
        description.date = data['date']
        description.ville = data['ville']
        description.description = data['description']
        db.session.commit()
        return jsonify({'message': 'Description updated!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/descriptions/<int:id>', methods=['DELETE'])
@jwt_required()  # Protection JWT
def delete_description(id):
    try:
        description = Description.query.get(id)
        if description is None:
            return jsonify({'error': 'Description not found'}), 404
        db.session.delete(description)
        db.session.commit()
        return jsonify({'message': 'Description deleted!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/artistes', methods=['GET'])
def get_artistes():
    try:
        artistes = Artiste.query.all()
        artistes_json = []
        for artiste in artistes:
            artistes_json.append({
                'id': artiste.id,
                'nom': artiste.nom,
                'genre_musical': artiste.genre_musical
            })
        return jsonify(artistes_json)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/artistes', methods=['POST'])
@jwt_required()  # Protection JWT
def add_artiste():
    try:
        data = request.get_json()
        artiste = Artiste(
            nom=data['nom'],
            genre_musical=data['genre_musical']
        )
        db.session.add(artiste)
        db.session.commit()
        return jsonify({'message': 'Artiste added!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/artistes/<int:id>', methods=['GET'])
def get_artiste(id):
    try:
        artiste = Artiste.query.get(id)
        if artiste is None:
            return jsonify({'error': 'Artiste not found'}), 404
        return jsonify({
            'id': artiste.id,
            'nom': artiste.nom,
            'genre_musical': artiste.genre_musical
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/artistes/<int:id>', methods=['PUT'])
@jwt_required()  # Protection JWT
def update_artiste(id):
    try:
        artiste = Artiste.query.get(id)
        if artiste is None:
            return jsonify({'error': 'Artiste not found'}), 404
        data = request.get_json()
        artiste.nom = data['nom']
        artiste.genre_musical = data['genre_musical']
        db.session.commit()
        return jsonify({'message': 'Artiste updated!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/artistes/<int:id>', methods=['DELETE'])
@jwt_required()  # Protection JWT
def delete_artiste(id):
    try:
        artiste = Artiste.query.get(id)
        if artiste is None:
            return jsonify({'error': 'Artiste not found'}), 404
        db.session.delete(artiste)
        db.session.commit()
        return jsonify({'message': 'Artiste deleted!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(HTTPException)
def handle_exception(e):
    response = e.get_response()
    response.data = jsonify({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response

if __name__ == '__main__':
    app.run(debug=True)
