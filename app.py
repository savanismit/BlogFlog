from flask import request, Flask, session, flash, render_template, url_for, redirect, flash 
from werkzeug.security import generate_password_hash,check_password_hash
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
from flask_ckeditor import CKEditor
import yaml
import os

app = Flask(__name__)
Bootstrap(app)
ckeditor = CKEditor(app)

db = yaml.load(open('db.yaml'), Loader=yaml.FullLoader)
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_PASSWORD'] = db['mysql_pass']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

app.config['SECRET_KEY'] = os.urandom(24)

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM blog")
    if result > 0:
        blogs = cur.fetchall()
        cur.close()
        return render_template('index.html',blogs = blogs)
    cur.close()
    return render_template('index.html',blogs = None)

@app.route('/blogs/<int:id>/')
def blogs(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT *FROM blog WHERE blog_id = {}".format(id))
    if result > 0 :
        blog = cur.fetchone()
        return render_template('blogs.html',blog = blog)
    return 'Blog not found!'

@app.route('/searchindex/<string:author>/')
def searchindex(author):
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT *FROM blog where author = {}".format(author))
        if result > 0:
            blogs = cur.fetchall()
            cur.close()
            return render_template('searchindex.html',blogs = blogs)
    cur.close()
    return render_template('searchindex.html',blogs = None)

@app.route('/register/', methods= ['GET','POST'])
def register():
    if request.method == 'POST':
        form = request.form
        if form['passw'] != form['cpass']:
            flash('Passwords do not match! Try again.', 'danger')
            return render_template('register.html')
        cur = mysql.connection.cursor()
        #password = generate_password_hash(password)
        #cpassword = generate_password_hash(cpassword)
        cur.execute("INSERT INTO user(f_name,l_name,user_name,email,gender,password,cpassword) VALUES(%s, %s, %s, %s, %s, %s, %s)",(form['f_name'],form['l_name'],form['user_name'],form['email'],form['gender'],form['passw'],form['cpass']))             
        mysql.connection.commit()
        cur.close()
        return redirect('/login/') 
    return render_template('register.html')

@app.route('/login/', methods= ['GET','POST'])
def login():
    if request.method == 'POST':
        form = request.form
        user_name = form['user_name']
        cur = mysql.connection.cursor()
        result  = cur.execute("SELECT *FROM user WHERE user_name = %s", ([user_name]))

        if result > 0:
            user = cur.fetchone()
            if form['passw'] == user['password']:
                session['login'] = True
                session['f_name'] = user['f_name']
                session['l_name'] = user['l_name']
                flash('Welcome ' + session['f_name'] +'! You have been successfully logged in', 'success')
            else:
                cur.close()
                flash('Wrong Password!', 'danger')
                return render_template('login.html')
        else:
            cur.close()
            flash('User not registered!', 'danger')
            return render_template('login.html')
        cur.close()
        return redirect('/')
    return render_template('login.html')

@app.route('/write-blog/', methods= ['GET','POST'])
def write_log():
    if request.method == 'POST':
        blogpage = request.form
        title = blogpage['title']
        body = blogpage['body']
        author = session['f_name'] + ' ' + session['l_name']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO blog(title, author, body) VALUES(%s, %s, %s)",(title,author,body))
        mysql.connection.commit()
        cur.close()
        flash("Successfully posted new blog.","success")
        return redirect('/')
    return render_template('write.html')

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/my-blogs/')
def my_blogs():
    author = session['f_name'] + ' ' + session['l_name']
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT *FROM blog WHERE author = %s",[author])
    if result > 0:
        my_blogs = cur.fetchall()
        return render_template('my_blogs.html', my_blogs = my_blogs)
    else:
        return render_template('my_blogs.html', my_blogs = None)

@app.route('/edit-blog/<int:id>', methods= ['GET','POST'])
def edit_blog(id):
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        title = request.form['title']
        body = request.form['body']
        cur.execute("UPDATE blog SET title = %s, body = %s where blog_id = %s",(title,body,id))
        mysql.connection.commit()
        cur.close()
        flash('Blog updated successfully.','success')
        return redirect('/blogs/{}'.format(id))
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT *FROM blog WHERE blog_id = {}".format(id))
    if result > 0:
        blog = cur.fetchone()
        blog_form = {}
        blog_form['title'] = blog['title']
        blog_form['body'] = blog['body']
        return render_template('edit_blog.html', blog_form = blog_form)

@app.route('/delete-blog/<int:id>/')
def delete_blog(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM blog WHERE blog_id = {}".format(id))
    mysql.connection.commit()
    flash("Your blog has been deleted!",'success')
    return redirect('/my-blogs/')

@app.route('/logout/', methods= ['GET','POST'])
def logout():
    session.clear()
    flash("You have been logged out.",'info')
    return redirect('/')

#@app.errorhandler(404)
#def page_not_found(error):
#    return render_template('404.html', meta_title='404'), 404

if __name__ == '__main__':
    app.run(debug=True)