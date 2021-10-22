from flask import (
    Flask, 
    render_template, 
    request, 
    redirect,
    session,
    Response,
    jsonify
    )
import logging
from queue import Queue
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import sys, datetime, json, base64

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../db.sqlite"
app.config["SECRET_KEY"] = "SECRET"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    added = db.Column(db.DateTime(timezone=True), default=datetime.datetime.now())

class Posts(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    added_date = db.Column(db.DateTime(timezone=True), default=datetime.datetime.now())
    content = db.Column(db.String(5000), nullable=False)
    title = db.Column(db.String(100), nullable=False, unique=True)
    approved = db.Column(db.Boolean(), nullable=False, default=False)
    approved_by = db.Column(db.Integer, db.ForeignKey(User.id), nullable=True)
    approved_date = db.Column(db.DateTime(timezone=True), nullable=True)
    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    

# db.create_all()
# sys.exit()

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=0, max=100)], render_kw={"placeholder":"Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=0, max=100)], render_kw={"placeholder":"Password"})
    submit = SubmitField("Login")

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=0, max=100)], render_kw={"placeholder":"Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=0, max=100)], render_kw={"placeholder":"Password"})
    password2 = PasswordField(validators=[InputRequired(), Length(min=0, max=100)], render_kw={"placeholder":"Password"})
    submit = SubmitField("Login")
    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError("user already exists")


@app.route("/")
@login_required
def hello_world():
    print(queue_list)
    username = current_user.username

    return f"<p>Hello, World! ---> {username}</p>"

@app.route("/logout")
@login_required
def logout():
    logout_user()
    if session.get('session'):
        # prevent flashing automatically logged out message
        del session['was_once_logged_in']
    return redirect('/login')
    #return render_template("mainpage.html")


@app.route("/restricted")
@login_required
def restricted():
    return "<p>restricted area!</p>"

@app.route("/accept/<int:id_post>", methods=["POST"])
@login_required
def accept(id_post):
    txt = request.data.decode("utf-8")

    if txt != "{}":
        data = json.loads(txt)
        txt = data.get("text")
        title = data.get("title")
        a_user = Posts.query.filter_by(id=id_post).one()
        a_user.content = txt
        db.session.commit()
        
        q = queue_list.get("api2gen")
        req = {
        "text": txt,
        "title": title
        }
        print(req)
        print(q)
        q.put(req)




    return "<p>restricted area!</p>"


@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                print(request.args)
                return redirect("/")

        return render_template('login.html', form=form)
    return render_template('login.html', form=form)

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pass = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_pass)
        db.session.add(new_user)
        db.session.commit()
   
    return render_template("register.html", form=form)


@app.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    qr = Posts.query.filter(Posts.approved != True).order_by(Posts.id.desc())
    res = []
    print(qr)
    for elem in qr:
        res.append(elem.as_dict())
        #res.append(json_parser(["id", "added_date", "title","content"], res))
    print(qr)


    # return jsonify(res)
    # return Response(f"{res}")
    return render_template("mainpage.html", posts=res)


def json_parser(headers, txt):
    dct = list()
    tmp = {}
    for elem in txt:
        for col in headers:
            # print(elem.content)
            if col == "content":
                x = eval(f"elem.{col}")
                # x = base64.b64decode(x)
                x = x.decode("utf-8")
                tmp[col] = str(x)
            elif col == "title":
                tmp[col] = str(eval(f"elem.{col}"))
                tmp["thumb"] = str("thumbnails/"+eval(f"elem.{col}")+ "_thumbnails.png")

            else:
                tmp[col] = str(eval(f"elem.{col}"))

        #dct.append(tmp)
    return tmp
        #return json.dumps(dct)


def back_server(q_list, host="0.0.0.0", port=12345):
    global queue_list
    queue_list = q_list

    app.run(host=host, port=port)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=12345)

#todo 
# clean up this shitty code