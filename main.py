import flask
from flask import Flask, request
from flask.views import MethodView

from sqlalchemy import exc
from sqlalchemy import Column, String, DateTime, Integer, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import pydantic

app = Flask('app')
PG_DSN = 'postgresql://admin:admin@127.0.0.1:5001/flask_db'
db_engine = create_engine(PG_DSN)
Base = declarative_base()
Session = sessionmaker(bind=db_engine)


@app.route('/home')
def home():
    return flask.jsonify({'status': 'works'})


'''Models'''


class AnnounceModel(Base):
    __tablename__ = 'announce'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=False)
    user = Column(Integer, nullable=False, default=1)
    create_time = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {'id': self.id,
                'create_time': str(self.create_time),
                'title': self.title,
                'description': self.description,
                'user': self.user,
                }


Base.metadata.create_all(db_engine)


'''Validators'''


class AnnounceValidator(pydantic.BaseModel):
    title: str
    description: str
    user: int


'''Views'''


class AnnounceView(MethodView):

    def post(self):
        try:
            validated_data = AnnounceValidator(**request.json).dict()
        except pydantic.ValidationError as er:
            raise HttpError(400, er.errors())
        with Session() as session:
            new_announce = AnnounceModel(**validated_data)
            session.add(new_announce)
            session.commit()
            return flask.jsonify({'id': new_announce.id})

    def get(self, announce_id: int):
        with Session() as session:
            try:
                announce = session.query(AnnounceModel).filter(AnnounceModel.id == announce_id).one()
            except exc.NoResultFound as er:
                raise HttpError(404, str(er))
            response = announce.to_dict()
            return flask.jsonify(response)

    def patch(self, announce_id: int):
        updated_data = request.json
        with Session() as session:
            try:
                session.query(AnnounceModel).filter(AnnounceModel.id == announce_id).one()#.update(updated_data)
            except exc.NoResultFound as er:
                raise HttpError(404, str(er))
            session.query(AnnounceModel).filter(AnnounceModel.id == announce_id).update(updated_data)
            session.commit()
            return flask.jsonify(updated_data)

    def delete(self, announce_id: int):
        with Session() as session:
            try:
                announce = session.query(AnnounceModel).filter(AnnounceModel.id == announce_id).one()
            except exc.NoResultFound as er:
                raise HttpError(404, str(er))
            session.delete(announce)
            session.commit()
        return flask.jsonify({'result': 'Object deleted'})


'''Exceptions'''


class HttpError(Exception):

    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message


@app.errorhandler(HttpError)
def handle_http_error(error):
    response = flask.jsonify({'message': error.message})
    response.status_code = error.status_code
    return response


'''Bindings'''

app.add_url_rule(
    '/announce/', view_func=AnnounceView.as_view('announce_api_post'), methods=['POST'])
app.add_url_rule(
    '/announce/<int:announce_id>', view_func=AnnounceView.as_view('announce_api_get'), methods=['GET'])
app.add_url_rule(
    '/announce/<int:announce_id>', view_func=AnnounceView.as_view('announce_api_path'), methods=['PATCH'])
app.add_url_rule(
    '/announce/<int:announce_id>', view_func=AnnounceView.as_view('announce_api_delete'), methods=['DELETE'])


app.run()
