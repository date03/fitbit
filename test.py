import base64
import hashlib
import random
import requests
import secrets
import string
import yaml  # PyYAML

from flask import Flask, request, session


# 設定ファイルの読み込み
with open('./secret.yaml') as f:
    secret = yaml.safe_load(f)

# Flaskの基本設定
app = Flask(__name__)
app.secret_key = secret['flask']['secret_key']  # sessionを用いる場合、必須


# 文字列をBase64URLへエンコード
def base64urlencode(code):
    b64 = base64.b64encode(code)
    b64_str = str(b64)[2:-1]
    b64url = b64_str.translate(str.maketrans({'+': '-', '/': '_', '=': ''}))

    return b64url


@app.get("/")
def top():
    # Step1: code_verifierとcode_challengeの取得
    code_verifier = ''.join(secrets.choice(string.digits)
                            for _ in range(random.randint(43, 128)))
    session["code_verifier"] = code_verifier
    code_challenge = base64urlencode(
        hashlib.sha256(code_verifier.encode()).digest())

    # Step2: 認証ページで認証してもらう
    # https://dev.fitbit.com/build/reference/web-api/authorization/authorize/
    authorization_url = f"\
https://www.fitbit.com/oauth2/authorize?\
&response_type=code\
&client_id={secret['fitbit']['client_id']}\
&redirect_uri=http%3A%2F%2Flocalhost%3A56565%2Fcallback\
&code_challenge={code_challenge}\
&code_challenge_method=S256\
&scope=activity%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20social%20weight\
&expires_in=86400"

    return f"<a href={authorization_url}>認証</a>"


@app.get("/callback")
def callback():
    # Step3: 認証コードの取得
    # 認証ページで許可が押されるとこのページへ遷移
    authorization_code = request.args.get('code')

    # Step4: アクセストークンとリフレッシュトークンの取得準備
    # https://dev.fitbit.com/build/reference/web-api/authorization/oauth2-token/
    headers = {
        'Authorization': 'Basic ' + str(base64.b64encode(f"{secret['fitbit']['client_id']}:{secret['fitbit']['client_secret']}".encode()))[2:-1],
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = f"client_id={secret['fitbit']['client_id']}&code={authorization_code}&code_verifier={session['code_verifier']}&grant_type=authorization_code&redirect_uri=http%3A%2F%2Flocalhost%3A56565%2Fcallback"

    # Step5: アクセストークンとリフレッシュトークンの取得
    tokens = requests.post(
        'https://api.fitbit.com/oauth2/token', headers=headers, data=data)

    return tokens.content


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=56565, debug=True)
