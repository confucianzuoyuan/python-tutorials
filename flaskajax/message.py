from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask import request, jsonify
import pymysql
pymysql.install_as_MySQLdb()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost:3306/messageboard'
db = SQLAlchemy(app)

class Message(db.Model):
    __tablename__ = "message"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    email = db.Column(db.String(120))
    useraddress = db.Column(db.String(400))
    messagetext = db.Column(db.String(400))

    def __repr__(self):
        return '<Message %r>' % self.username

@app.route('/', methods=['GET', 'POST'])
def message():
    if request.method == 'GET':
        print(Message.query.all())
        return render_template('message.html')
    if request.method == 'POST':
        try:
            data = request.get_data()
            from werkzeug.urls import url_decode
            data = url_decode(data)
            print('data: ', data)
            username = data.get('username', 0)
            email = data.get('email', 0)
            useraddress = data.get('useraddress', 0)
            messagetext = data.get('messagetext', 0)
            message = Message(username=username, email=email, useraddress=useraddress, messagetext=messagetext)
            db.session.add(message)
            db.session.commit()
            return jsonify(res=200)
        except Exception as e:
            print('e: ', e)
            return jsonify(res=500)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8888)