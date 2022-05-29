import base64
import hashlib
import random
import requests
import secrets
import string
import yaml

from flask import request, session, redirect, url_for

from database import User, app, db


# 設定ファイルの読み込み
with open('./secret.yaml') as f:
    secret = yaml.safe_load(f)


# 文字列をBase64URLへエンコード
def base64urlencode(code):
    b64 = base64.b64encode(code)
    b64_str = str(b64)[2:-1]
    b64url = b64_str.translate(str.maketrans({'+': '-', '/': '_', '=': ''}))

    return b64url


@app.get("/")
def top():
    # Step1: code_verifierとcode_challengeの作成
    code_verifier = ''.join(secrets.choice(string.digits)
                            for _ in range(random.randint(43, 128)))
    session['code_verifier'] = code_verifier
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
    # 認証ページで許可が押されるとこのページへ遷移

    # Step3: 認証コードの取得
    authorization_code = request.args.get('code')
    if authorization_code is None:  # ?code= がなければトップへ
        return redirect(url_for('top'))

    # Step4: アクセストークンとリフレッシュトークン取得のためのURLを構築
    # https://dev.fitbit.com/build/reference/web-api/authorization/oauth2-token/
    headers = {
        'Authorization': 'Basic ' + str(base64.b64encode(f"{secret['fitbit']['client_id']}:{secret['fitbit']['client_secret']}".encode()))[2:-1],
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = f"client_id={secret['fitbit']['client_id']}&code={authorization_code}&code_verifier={session['code_verifier']}&grant_type=authorization_code&redirect_uri=http%3A%2F%2Flocalhost%3A56565%2Fcallback&expires_in=31536000"

    # Step5: アクセストークンとリフレッシュトークンの取得
    tokens = requests.post(
        'https://api.fitbit.com/oauth2/token', headers=headers, data=data)

    # 取得できた場合
    if tokens.status_code == 200:
        token_dict = tokens.json()  # json -> dict
        user_id = token_dict['user_id']                 # user_id
        access_token = token_dict['access_token']       # access_token
        refresh_token = token_dict['refresh_token']     # refresh_token

        # DBにすでに存在するか検索
        user = User.query.filter_by(user_id=user_id).one_or_none()

        if user is not None:        # 存在していた場合
            session['user_id'] = user_id

        else:                       # 存在しなかった場合
            # DBにユーザを記録
            user = User(user_id, access_token, refresh_token)
            try:
                db.session.add(user)
                db.session.commit()
            except:
                return redirect(url_for('top'))

            session['user_id'] = user_id

        return redirect(url_for('apitest'))

    # 取得できなかった場合
    else:
        return redirect(url_for('top'))


@app.get("/apitest")
def apitest():
    # Step6 心拍数の取得(テスト)
    # https://dev.fitbit.com/build/reference/web-api/heartrate-timeseries/get-heartrate-timeseries-by-date-range/

    # user_idが存在しない場合、トップページへ
    try:
        user_id = session['user_id']
    except:
        return redirect(url_for('top'))

    # DBからアクセストークンの取得
    user = User.query.filter_by(user_id=user_id).one_or_none()
    access_token = user.access_token

    # 心拍数取得用のURLの構築
    headers = {
        'accept': 'Basic ' + 'application/json',
        'authorization': 'Bearer '+access_token,
        'accept-language': 'ja_JP',
    }

    heart_rate = requests.get(
        f"https://api.fitbit.com/1/user/{user_id}/activities/heart/date/2022-05-01/today.json", headers=headers)

    return heart_rate.json()


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=56565, debug=True)
