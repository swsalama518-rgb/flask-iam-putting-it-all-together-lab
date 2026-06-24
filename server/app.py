#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe, UserSchema, RecipeSchema

class Signup(Resource):
    def post(self):
        try:
            data = request.get_json()

            user = User(
                username=data['username'],
                image_url=data.get('image_url'),
                bio=data.get('bio')
            )
            user.password_hash = data['password']

            db.session.add(user)
            db.session.commit()

            session['user_id'] = user.id

            return UserSchema().dump(user), 201

        except IntegrityError:
            db.session.rollback()
            return {"error": "422 Unprocessable Entity"}, 422

        except Exception as e:
            return {"error": str(e)}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get("user_id")

        if user_id:
            user = User.query.get(user_id)
            return UserSchema().dump(user), 200

        return {"error": "401 Unauthorized"}, 401

class Login(Resource):
    def post(self):
        data = request.get_json()

        user = User.query.filter_by(username=data['username']).first()

        if user and user.authenticate(data['password']):
            session['user_id'] = user.id
            return UserSchema().dump(user), 200

        return {"error": "401 Unauthorized"}, 401

class Logout(Resource):
    def delete(self):
        if session.get("user_id"):
            session['user_id'] = None
            return {}, 204

        return {"error": "401 Unauthorized"}, 401

class RecipeIndex(Resource):

    def get(self):
        if not session.get("user_id"):
            return {"error": "401 Unauthorized"}, 401

        recipes = Recipe.query.all()
        return RecipeSchema(many=True).dump(recipes), 200

    def post(self):
        if not session.get("user_id"):
            return {"error": "401 Unauthorized"}, 401

        try:
            data = request.get_json()

            recipe = Recipe(
                title=data["title"],
                instructions=data["instructions"],
                minutes_to_complete=data.get("minutes_to_complete"),
                user_id=session["user_id"]
            )

            db.session.add(recipe)
            db.session.commit()

            return RecipeSchema().dump(recipe), 201

        except ValueError as e:
            return {"errors": [str(e)]}, 422
api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)