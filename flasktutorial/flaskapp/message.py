from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form, BooleanField, StringField, PasswordField, validators
from flask import request
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

class MessageForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    useraddress = StringField('User Address', [validators.Length(min=0, max=400)])
    messagetext = StringField('Message Text', [validators.Length(min=0, max=400)])

@app.route('/', methods=['GET', 'POST'])
def message():
    form = MessageForm(request.form)
    if request.method == 'GET':
        print(Message.query.all())
        return render_template('message.html', form=form)
    if request.method == 'POST' and form.validate():
        message = Message(username=form.username.data, email=form.email.data, useraddress=form.useraddress.data, messagetext=form.messagetext.data)
        db.session.add(message)
        db.session.commit()
        form.username.data = ''
        form.email.data = ''
        form.useraddress.data = ''
        form.messagetext.data = ''
        return render_template('message.html', form=form)


if __name__ == "__main__":
    app.run()