from flask import request, render_template, jsonify
from . import app, db
from .models import User, DogFact, Comment
from .auth import basic_auth, token_auth


@app.route("/")
def index():
    return render_template('index.html')


@app.route('/users', methods=['POST'])
def create_user():
    if not request.is_json:
        return {'error': 'Your content-type must be application/json'}, 400
    data = request.json

    required_fields = ['firstName', 'lastName','username', 'email', 'password']
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    if missing_fields:
        return {'error': f"{', '.join(missing_fields)} must be in the request body"}, 400


    first_name = data.get('firstName')
    last_name = data.get('lastName')
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    check_users = db.session.execute(db.select(User).where( (User.username == username) | (User.email == email) )).scalars().all()
    if check_users:
        return {'error': "A user with that username and/or email already exists"}, 400

    new_user = User(first_name = first_name, last_name = last_name, username=username, email=email, password=password)
    
    return new_user.to_dict()

@app.route('/token')
@basic_auth.login_required
def get_token():
    user = basic_auth.current_user()
    # return {'token': user.get_token(), 'userId': user.id}
    return user.get_token()

@app.route('/users/me')
@token_auth.login_required
def get_me():
    user = token_auth.current_user()
    return user.to_dict()


@app.route('/dog_facts')
def get_facts():
    select_stmt = db.select(DogFact)
    # search = request.args.get('search')
    # if search:
    #     select_stmt = select_stmt.where(DogFact.title.ilike(f"%{search}%"))
    facts = db.session.execute(select_stmt).scalars().all()
    return [f.to_dict() for f in facts]


@app.route('/dog_facts/<int:fact_id>')
def get_fact(fact_id):
    fact = db.session.get(DogFact, fact_id)
    if fact:
        return fact.to_dict()
    else:
        return {'error': f"Fact with an ID of {fact_id} does not exist"}, 404

#create facts
@app.route('/dog_facts', methods=['POST'])
@token_auth.login_required
def create_dog_fact():
    if not request.is_json:
        return {'error': 'Your content-type must be application/json'}, 400
    
    data = request.json
    
    required_fields = ['title','fact']
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    if missing_fields:
        return {'error': f"{', '.join(missing_fields)} must be in the request body"}, 400
    
    title = data.get('title')
    fact = data.get('fact')


    current_user = token_auth.current_user()
    new_dog_fact = DogFact(title = title, fact=fact, user_id=current_user.id)
    return new_dog_fact.to_dict(), 201

@app.route('/dog_facts/<int:fact_id>', methods=['PUT'])
@token_auth.login_required
def get_dog_facts(fact_id):
    if not request.is_json:
        return {'error': 'You content-type must be application/json'}, 400
    fact = db.session.get(DogFact, fact_id)
    if fact is None:
        return {'error': f"Fact with ID #{fact_id} does not exist"}, 404
    current_user = token_auth.current_user()
    if current_user is not fact.user:
        return {'error': 'This is not your post. You do not have permission to edit'}, 403
    data = request.json
    fact.update(**data)
    return fact.to_dict()


# @app.route('/favorite_facts')
# def get_fav_facts(user_id):
#     select_stmt = db.select(DogFact)
#     facts = db.session.execute(select_stmt).scalars().all()
#     return [f.to_dict() for f in facts]


# @app.route('/dog_facts/<int:user_id>/favorite_facts', methods=['GET'])
# @token_auth.login_required
# def get_favorite_facts(user_id):
#     user = db.session.get(user_id)
#     favorite_facts = user.favorite_facts
#     return jsonify([fact.to_dict() for fact in favorite_facts]), 200

# @app.route('/dog_facts/<int:user_id>/favorite_facts', methods=['POST'])
# @token_auth.login_required
# def save_favorite_fact(user_id):
#     user = db.session.get(user_id)
#     data = request.json
#     if 'fact' not in data:
#         return {'error': 'Missing fact field'}, 400
#     fact = DogFact(fact = data['fact'], user=user)
#     db.session.add(fact)
#     db.session.commit()
#     return {'success': 'Favorite fact saved successfully'}, 201


@app.route('/dog_facts/<int:fact_id>', methods=['DELETE'])
@token_auth.login_required
def delete_fact(fact_id):
    fact = db.session.get(DogFact, fact_id)
    if fact is None:
        return {'error': f"Fact with ID #{fact_id} does not exist"}, 404
    current_user = token_auth.current_user()
    if current_user is not fact.user:
        return {'error': "This is not your post. You do not have permission to delete"}, 403
    fact.delete()
    return {'success': "Post has been successfully deleted"}, 200


@app.route('/dog_facts/<int:fact_id>/comments', methods=['POST'])
@token_auth.login_required
def create_comment(fact_id):
    if not request.is_json:
        return {'error': 'Your content-type must be application/json'}, 400
    fact = db.session.get(DogFact, fact_id)
    if fact is None: 
        return {'error': f"Fact {fact_id} does not exist"}, 404
    
    data = request.json
    required_fields = ['body']
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    
    if missing_fields:
        return {'error': f"{', '.join(missing_fields)} must be present in the request body"}, 400
    body = data.get('body')
    current_user = token_auth.current_user()
    new_comment = Comment(body=body, user_id=current_user.id, fact_id=fact.id)
    return new_comment.to_dict(), 201

@app.route('/dog_facts/<int:fact_id>/comments/<int:comment_id>', methods=['DELETE'])
@token_auth.login_required
def delete_comment(fact_id, comment_id):
    fact = db.session.get(DogFact, fact_id)
    if fact is None:
        return {'error': f"Fact {fact_id} does not exist"}, 404
    comment = db.session.get(Comment, comment_id)
    if comment is None:
        return {'error': f"Comment {comment_id} does not exist"}, 404
    if comment.fact_id != fact.id:
        return {'error' : f"Comment #{comment_id} is not associated with Fact #{fact_id}"}, 403
    current_user = token_auth.current_user()
    if comment.user != current_user:
        return {'error': 'You do not have permission to delete this comment'}, 403
    comment.delete()
    return {'success': "Comment has been successfully deleted"}, 200

  
