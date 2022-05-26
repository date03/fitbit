from flask import Flask, request
import yaml
import requests
import base64
import secrets
import string
import hashlib


app = Flask(__name__)

with open('./secret.yaml') as f:  # 設定ファイルの読み込み
    secret = yaml.safe_load(f)


def verifier_gen(size=64):
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    chars += '-_'
    return ''.join(secrets.choice(chars) for x in range(size))


code_verifier = b'CJ3dGgqKRB6n1U19YfEy63A_wLe0AsFR4Wq0T_RSpwgoHRL7jbCQELfuqG4bcvDt'


@app.get("/")
def top():
    # code_verifier = verifier_gen().encode()
    print(code_verifier)

    code_challenge = hashlib.sha256(code_verifier).hexdigest()

    oauth1_url = f"\
https://www.fitbit.com/oauth2/authorize?\
&response_type=code\
&client_id={secret['fitbit']['client_id']}\
&redirect_uri=http%3A%2F%2Flocalhost%3A56565%2Fcallback\
&code_challenge={code_challenge}\
&code_challenge_method=S256\
&scope=activity%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20social%20weight\
&expires_in=31536000"

    return f"<a href={oauth1_url}>認証</a>"


@app.get("/callback")
def callback():
    headers = {
        'Authorization': 'Basic ' + str(base64.b64encode(f"{secret['fitbit']['client_id']}:{secret['fitbit']['client_secret']}".encode()))[2:-1],
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = f"client_id={secret['fitbit']['client_id']}&code={request.args.get('code')}&code_verifier={str(code_verifier)[2:-1]}&grant_type=authorization_code&redirect_uri=http%3A%2F%2Flocalhost%3A56565%2Fcallback"
    print(data)
    response = requests.post(
        'https://api.fitbit.com/oauth2/token', headers=headers, data=data)

    return response.content


@app.get("/callback2")
def callback2():
    return "ok"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=56565, debug=True)
