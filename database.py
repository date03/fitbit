import yaml
import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 設定ファイルの読み込み
with open('./secret.yaml') as f:
    secret = yaml.safe_load(f)

# Flaskの基本設定
app = Flask(__name__)
app.secret_key = secret['flask']['secret_key']  # sessionを用いる場合、必須
app.permanent_session_lifetime = datetime.timedelta(hours=3)  # sessionの有効期限

# DBの基本設定
app.config['SQLALCHEMY_DATABASE_URI'] = secret['database_uri']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    user_id = db.Column(db.String(50), primary_key=True)    # user_id
    access_token = db.Column(db.String(1000))                # access_token
    refresh_token = db.Column(db.String(1000))               # refresh_token

    def __init__(self, user_id, access_token, refresh_token):
        self.user_id = user_id
        self.access_token = access_token
        self.refresh_token = refresh_token


db.create_all()
