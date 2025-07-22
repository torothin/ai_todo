from flask import Flask, render_template, request, redirect, url_for, session
import boto3
import uuid
from authlib.integrations.flask_client import OAuth
import os
from dotenv import load_dotenv


app = Flask(__name__)
load_dotenv()

client = boto3.client('cognito-idp', region_name='us-west-2')
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
table = dynamodb.Table('Todos')

app.secret_key = os.urandom(24)  # Use a secure random key in production

oauth = OAuth(app)

oauth.register(
  name='oidc',
  authority='https://cognito-idp.us-west-2.amazonaws.com/us-west-2_iew2zwYMY',
  client_id='7588mruoo6qr8t3pghkdhi2upa',
  client_secret=os.environ.get('COGNITO_CLIENT_SECRET'),
  server_metadata_url='https://cognito-idp.us-west-2.amazonaws.com/us-west-2_iew2zwYMY/.well-known/openid-configuration',
  client_kwargs={'scope': 'email openid phone'}
)

@app.route('/')
@app.route("/index")
def index():
    user = getUser()
    if not user:
        return f'Welcome! Please <a href="/login">Login</a>.'
    
    response = table.scan()
    todos = response.get('Items', [])
    user = getUser()
    filtered_todos = list(filter(lambda obj: obj["user"] != user, todos))
    return render_template('index.html', todos=filtered_todos)
    

@app.route('/add', methods=['POST'])
def add():

    todo = request.form.get('todo')
    if todo:
        Item={'user':getUser()["sub"],'id': str(uuid.uuid4()), 'task': todo}
        table.put_item(Item=Item)
    return redirect(url_for('index'))

@app.route('/delete/<item_id>')
def delete(item_id):

    table.delete_item(Key={'id': item_id})
    return redirect(url_for('index'))

@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    return oauth.oidc.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    token = None
    user = None

    token = oauth.oidc.authorize_access_token()
    user = token['userinfo']
    session['user'] = user
    return redirect(url_for('index'))

@app.route('/protected')
def protected():
    if isActiveToken():
        return redirect('/')
    else:
        return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

def isActiveToken():
    return 'access_token' in session

def getUser():
    return session.get('user')

if __name__ == "__main__":
    app.run(host='0.0.0.0', ssl_context='adhoc', port=443)
