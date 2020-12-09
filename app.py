import requests
import sqlite3

from flask import Flask, redirect, render_template, request, url_for
from peewee import BooleanField, CharField, IntegerField, IntegrityError, ForeignKeyField, Model, PostgresqlDatabase, SqliteDatabase, TextField


db = SqliteDatabase('phonebook.db')

class BaseModel(Model):
    class Meta:
        database = db


class Users(BaseModel):
    username = CharField(unique=True)
    password = CharField()
    email = CharField(unique=True)
    signin = BooleanField(default=False)

    class Meta:
        table_name = 'users'


class Phones(BaseModel):
    name = TextField()
    phonenumber = TextField(unique=True)

    class Meta:
        table_name = 'phonebook'


class PhonesUsers(BaseModel):
    user_id = ForeignKeyField(Users)
    phone_id = ForeignKeyField(Phones)

    class Meta:
        table_name = 'phone_users'


TABLES = [
    Phones, PhonesUsers, Users
]

with db.connection_context():
    db.create_tables(TABLES, safe=True)
    db.commit()


app = Flask(__name__)



@app.before_request
def _db_connect():
    db.connect()


@app.teardown_request
def _db_close(_):
    if not db.is_closed():
        db.close()


@app.route('/', methods=['GET'])
def login():
    try:
        if request.method == "GET":
            e_mail = request.args.get("Email")
            if not e_mail:
                return render_template('index.html')
            password = request.args.get("Password")
            result = Users.select(Users.id).where((Users.email == e_mail) & (Users.password == password)).get()
            if result:
                result.signin = True
                result.save()
                return render_template('index.html', result=result, username ="")
            else:
                return render_template('index.html', message = "Please register")
    except:
        return render_template('index.html')


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        username = request.form["Username"]
        password = request.form["Password"]
        e_mail = request.form["Email"]
        try:
            Users.create(username=username, password=password, email=e_mail)
        except IntegrityError:
            return render_template('signup.html', username = username, message="Choose another")
        result = True
        return render_template('signup.html', result=result, username = username, message="added successfully")
    else:
        return render_template('signup.html', username = "", message="")


@app.route('/addname', methods=['POST', 'GET'])
def addname():
    if request.method == "POST":
        name = request.form["names"]
        if not name:
            return render_template('addname.html')
        else:
            phonenumber = request.form["phones"]
        try:
            Phones.create(name=name, phonenumber=phonenumber)
            phone_id = Phones.select(Phones.id).order_by(Phones.id.desc()).limit(1).get()
            signin = Users.select(Users.id).where(Users.signin == True).get()
            PhonesUsers.create(user_id=signin, phone_id=phone_id)
        except IntegrityError:
            return render_template('addname.html', username = name, message="name exist, Please try another")
        return render_template('addname.html', message="added successfully")
    else:
        return render_template('addname.html')


@app.route('/search', methods=['GET'])
def search():
    try:
        if request.method == "GET":
            name = request.args.get("names")
            if not name:
                return render_template('search.html')
            result = Phones.select(Phones.phonenumber).where(Phones.name == name).get()
            return render_template('search.html', name = name, phonenumber = result.phonenumber, result=result)
    except:
        return render_template('search.html', phonenumber = "", message = "No such name in your phonebook, You may click on 'Add to my phonebook'")


@app.route('/deletename', methods=['GET'])
def deletename():
    try:
        if request.method == "GET":
            name = request.args.get("names")
            if not name:
                return render_template('deletename.html')
            result = Phones.select(Phones.id).where(Phones.name == name).get()
            result.delete_instance()
            result.save()
            return render_template('deletename.html', name=name, phonenumber = "")
    except:
        return render_template('deletename.html', phonenumber = "", message = "")


@app.route('/userphone')
def userphone():
    phone = (Phones.select().join(PhonesUsers, on=(PhonesUsers.phone_id == Phones.id)).join(Users, on=(Users.id == PhonesUsers.user_id)).where(Users.signin == 'True').order_by(Phones.name))
    return render_template('phonelist.html', phone=phone)


@app.route('/logout')
def logout():
    logged_user = Users.select(Users.id).where(Users.signin == True).get()
    logged_user.signin = False
    logged_user.save()
    return redirect(url_for("login"))


if __name__ == '__main__':
    app.run()