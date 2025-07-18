from flask import Flask, render_template, request, redirect, url_for
import boto3
import uuid

app = Flask(__name__)

dynamodb = boto3.resource('dynamodb', region_name='YOUR_REGION')
table = dynamodb.Table('Todos')

@app.route('/')
def index():
    response = table.scan()
    todos = response.get('Items', [])
    # Sort by creation time if desired, or leave as is
    return render_template('index.html', todos=todos)

@app.route('/add', methods=['POST'])
def add():
    todo = request.form.get('todo')
    if todo:
        table.put_item(Item={'id': str(uuid.uuid4()), 'task': todo})
    return redirect(url_for('index'))

@app.route('/delete/<item_id>')
def delete(item_id):
    table.delete_item(Key={'id': item_id})
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
