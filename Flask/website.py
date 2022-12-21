from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
#Kullanici Giriş Decorator

def login_required(f):    #Bunu flask decorator yazarak crtl c ctrl v yaptım
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için giriş yap","danger")
            return redirect(url_for("login"))
    return decorated_function

#Kullanıcı kayıt formu

class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.length(min=3 ,max=25)])
    username = StringField("Kullanici Adi",validators=[validators.length(min=5 ,max=25)])
    email = StringField("Email Adresi",validators=[validators.Email(message="Geçerli mail adresi gir la")])
    password= PasswordField("Parola:",validators=[
        validators.DataRequired(message="Parola belirleyiniz."),
        validators.EqualTo(fieldname= "confirm",message="Parola uyuşmuyor"),
    ])
    confirm = PasswordField("Parola Doğrula")

class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")

app=Flask(__name__)
app.secret_key= "aaa"
app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="atablog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"

mysql= MySQL(app)

@app.route("/")
def h():
    article=[
        {"id":1,"title":"Deneme1","content":"Deneme1İcerik"},
        {"id":2,"title":"Deneme2","content":"Deneme2İcerik"},
        {"id":3,"title":"Deneme3","content":"Deneme3İcerik"}
    ]
    return render_template("index.html", article = article)
@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/dashboard")
@login_required
def dashboard():
    cursor= mysql.connection.cursor()

    sorgu = "SELECT * FROM articles WHERE author = %s"

    result = cursor.execute(sorgu,(session["username"],))

    if result >0:
        articles =cursor.fetchall()
        return render_template("dashboard.html",articles=articles)

    else:
        return render_template("dashboard.html")


    #Kayıt olma

@app.route("/register", methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():   #Formda birşey yoksa anlamında
        name= form.name.data  #namedeki datayı al anlamında
        username= form.username.data
        email= form.email.data
        password= sha256_crypt.encrypt(form.password.data)  #parola şifrelendi

        cursor= mysql.connection.cursor()    #Burdaki mysql mysql= Myql(app) deki

        sorgu= "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(sorgu,(name,email,username,password))
        
        mysql.connection.commit()

        cursor.close()
        
        flash("Başarıyla ile kayıt oldunuz","success")    #success ya da danger

        return redirect(url_for("login"))  #redirect nereye gitmemizi söyler, url_for ise hangi yere
    else:
        return render_template("register.html",form=form)

        #Giriş yapma

@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)

    if request.method == "POST":
        username= form.username.data
        password_entered= form.password.data

        cursor= mysql.connection.cursor()

        sorgu= "SELECT * FROM users where username = %s"

        result = cursor.execute(sorgu,(username,))       #usarname i demet halinde göndermek lazım

        if result>0:
            data = cursor.fetchone()
            real_password = data["password"]  #userdaki password alanı
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla giriş yaptınız","success")

                session["logged_in"] = True
                session["username"] = username
                
                return redirect(url_for("h"))
            else:
                flash("Yanlış girdiniz","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor...","danger")
            return redirect(url_for("login"))

    return render_template("login.html",form=form) 

   #Logout

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("h"))  

@app.route("/article31/<string:id>")            #Bu komutu anladın dinamik url
def dss(id):
    return "article id:" + id

    #Makale görüntüleme
@app.route("/articles")
def articles():
    cursor = mysql.connect.cursor()

    sorgu =  "SELECT * FROM articles"

    result= cursor.execute(sorgu)  #Makale varsa 0 dan büyük sonuç döndürür result

    if result>0:
        articles= cursor.fetchall()

        return render_template("articles.html",articles=articles)     
    else:
        return render_template("articles.html")


   #Makale ekleme

@app.route("/addarticle",methods= ["GET","POST"])
def addarticle():
    form=ArticleForm(request.form)
    if request.method =="POST" and form.validate():  #validate true döndürrü doğruysa
        title=form.title.data #datasını aldık
        content=form.content.data
        
        cursor= mysql.connection.cursor()

        sorgu ="INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))  #author session oldu
        
        mysql.connection.commit()

        cursor.close()

        flash("Makale başarıyla eklendi","success")

        return redirect(url_for("dashboard"))

    return render_template("addarticle.html",form=form)

    #Makale Form

class ArticleForm(Form):
    title=StringField("Makale Başlığı",validators=[validators.Length(min = 3,max = 20)])
    content = TextAreaField("Makale İçeriği",validators=[validators.Length(min=3)])

#Detay Sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()

    sorgu= "SELECT * FROM articles WHERE id = %s"

    result = cursor.execute(sorgu,(id,))

    if result >0:
        article = cursor.fetchone()
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")
        #Makale Sile
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    sorgu= "Select * from articles where author = %s and id = %s"

    result= cursor.execute(sorgu,(session["username"],id))

    if result>0:
        sorgu2= "Delete from articles where id = %s"

        cursor.execute(sorgu2,(id,))

        mysql.connection.commit()

        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya izniniz yok","danger")
        return redirect(url_for("index"))
    #Makale Güncelleme
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def uptade(id):
    if request.method=="GET":
        cursor = mysql.connection.cursor()

        sorgu = "Select * from articles where id= %s and author = %s"

        result = cursor.execute(sorgu,(id,session["username"]))

        if result ==0:
            flash("Böyle bir makale yok veya böyle bir işleme yetkiniz yok","danger")
            return redirect(url_for(""))
        else:
            article = cursor.fetchone()

            form =ArticleForm()

            form.title.data= article["title"]

            form.content.data = article["content"]

            return render_template("uptade.html",form = form)

    else:
        #POST request
        form = ArticleForm(request.form)

        newtitle=form.title.data
        newcontent=form.content.data

        sorgu2= "UPDATE articles SET title = %s,content=%s WHERE id=%s"
        
        cursor= mysql.connection.cursor()

        cursor.execute(sorgu2,(newtitle,newcontent,id))

        mysql.connection.commit()

        flash("Makale başarıyla güncellendi","success")

        return redirect(url_for("dashboard"))
    #Arama URL

@app.route("/search", methods= ["GET","POST"])
def search():
    if request.method =="GET":
        return redirect(url_for("index"))
    else:
        keyword= request.form.get("keyword") #articles.html de input alanının adı keyword ne yazdıysan o keyword oluyo

        cursor= mysql.connection.cursor()

        sorgu = "Select * from articles where title like '%" + keyword + "%'"

        result= cursor.execute(sorgu)

        if result ==0:
            flash("Aranan kelimeye uygun makale bulunmadı...","warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()

            return render_template("articles.html",articles= articles)
if __name__ == "__main__":
    app.run(debug=True)
