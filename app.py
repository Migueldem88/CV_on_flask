import os
from flask import Flask, render_template, url_for, redirect, request, flash, session
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
import yaml
from flask_ckeditor import CKEditor
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash,check_password_hash




UPLOAD_FOLDER = "static/"
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app = Flask(__name__)

Bootstrap(app)

#DB configuration
db = yaml.safe_load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['SECRET_KEY'] = os.urandom(24)

#folder to save photos
UPLOAD_FOLDER = os.path.join('static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#Image folder to retrieve photo
IMAGE_FOLDER = '\static'
app.config['IMAGE_FOLDER'] = IMAGE_FOLDER

mysql=MySQL(app)

@app.route('/')
def index():
    cursor = mysql.connection.cursor()
    result_value = cursor.execute("SELECT * FROM general")
    if result_value > 0:
        entries = cursor.fetchall()
        cursor.close()
        return render_template('index.html', entries=entries)
    else:
        return render_template('index.html')


@app.route('/register/',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        user_details = request.form
        if user_details['password'] != user_details['confirmPassword']:
            flash('Passwords do not match! Try again','danger')
            return render_template('register.html')
        cursor = mysql.connection.cursor()

        cursor.execute("INSERT INTO users(username, FL_name, email, Admin, password) VALUES (%s, %s, %s, %s, %s)",
                           (user_details['username'],user_details['FL_name'],
                            user_details['email'],user_details['Admin'],
                            generate_password_hash(user_details['password'])))

        mysql.connection.commit()
        cursor.close()
        flash('Registraton successful! please login','success')
        return redirect('/login')

    return render_template('register.html')

@app.route('/login/',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user_details = request.form
        user_name = user_details['username']
        cursor = mysql.connection.cursor()
        results_value = cursor.execute("SELECT * FROM users WHERE username = %s",([user_name]))

        if results_value > 0:
            user = cursor.fetchone()
            if check_password_hash(user['password'],user_details['password']):
                session['login'] = True
                session['FL_name'] = user['FL_name']
                session['email'] = user['email']
                flash('Welcome' + session['FL_name'] + '!You have been successfully logged in','success')

            else:
                cursor.close
                flash('Password is incorrect!','danger')
                return render_template('login.html')

        else:
            cursor.close()
            flash(f"User doesn't exist", 'danger')
            return render_template('login.html')
        cursor.close()
        return redirect('/')
    return render_template('login.html')


@app.route('/add-new/',methods=['GET','POST'])
def add_new():
    if request.method == 'POST':
        new_employee = request.form
        cursor = mysql.connection.cursor()
        FL_name = session['FL_name']
        define_admin = cursor.execute("SELECT * FROM users WHERE Admin = 1 and FL_name = %s",([FL_name]))
        if define_admin:
            #admin = cursor.fetchone()
            cursor = mysql.connection.cursor()
            cursor.execute("INSERT INTO general(FirstLastName,profession,age,Tel,email) VALUES (%s, %s, %s, %s, %s)",\
                                (new_employee['FirstLastName'], new_employee['profession'], new_employee['age'],
                                 new_employee['Tel'],new_employee['email']))
            mysql.connection.commit()
            cursor.close()
            flash('New entry added','success')
            return redirect(url_for('index'))
        else:
            cursor.close
            flash('Only admin can make entries! Try again!!', 'danger')
            return render_template('index.html')
    return render_template('add_new.html')

@app.route('/add-detail/<int:id>',methods=['GET','POST'])
def add_detail(id):
    if request.method == 'POST':
        add_data = request.form
        cursor = mysql.connection.cursor()
        try:
            FL_name = session['FL_name']
            define_admin = cursor.execute("SELECT * FROM users WHERE Admin = 1 and FL_name = %s", ([FL_name]))
            if define_admin:
                result_value = cursor.execute("SELECT * FROM general WHERE CV_id={}".format(id))
                if result_value > 0:
                    cv = cursor.fetchone()
                    cursor.execute("INSERT INTO detailed(Education,Experience,Skills, Additional_information, CV_id) VALUES (%s, %s, %s, %s, %s)",
                                       (add_data['Education'],add_data['Experience'],add_data['Skills'],
                                        add_data['Additional_information'],add_data['CV_id']))

                    if int(add_data['CV_id']) == id:
                        mysql.connection.commit()
                        cursor.close()
                        flash('New entry added', 'success')
                        return redirect(url_for('index'))
                    else:
                        flash("CV id doesn't correspond", 'danger')
                        return redirect(url_for('index'))
                else:
                    flash("CV doesn't exist", 'danger')
                    return redirect(url_for('index'))
            else:
                cursor.close
                flash('Only admin can make entries! Try again!!', 'danger')
                return redirect(url_for('index'))
        except:
            flash('Entry cannot be made! Try again!!', 'danger')
            return redirect(url_for('index'))
    return render_template('add-detail.html')


@app.route('/cvs/<int:id>')
def cvs(id):
    cursor = mysql.connection.cursor()
    result_value = cursor.execute("SELECT * FROM detailed d INNER JOIN general g "
                                  "on d.CV_id = g.CV_id WHERE d.CV_id={}".format(id))

    if result_value>0:
        cv = cursor.fetchone()
        quer = cursor.execute("SELECT Filename FROM files WHERE CV_id = {}".format(id))
        res = cursor.fetchone()
        if res:
            print(res['Filename'])
            img = os.path.join(app.config['IMAGE_FOLDER'], res['Filename'])
            return render_template('CV.html', cv=cv, user_image=img)
        else:
            img = os.path.join(app.config['IMAGE_FOLDER'], 'no_image.jpg')
            return render_template('CV.html', cv=cv, user_image=img)

    else:
        cursor = mysql.connection.cursor()
        result_value = cursor.execute("SELECT * FROM general WHERE CV_id = {}".format(id))
        if result_value > 0:
            cv = cursor.fetchone()
            return render_template('CV2.html', cv=cv)
        flash('CV not found!', 'danger')
        return redirect(url_for('add_new'))



@app.route('/edit-general/<int:id>',methods=['GET','POST'])
def edit_general(id):
    if request.method=='POST':
        cursor = mysql.connection.cursor()
        Name = request.form['FirstLastName']
        age = request.form['age']
        Email = request.form['email']
        Phone = request.form['Tel']
        FL_name = session['FL_name']
        define_admin = cursor.execute("SELECT * FROM users WHERE Admin = 1 and FL_name = %s", ([FL_name]))
        if define_admin:
            cursor.execute("UPDATE general SET FirstLastName =%s, age = %s, email = %s, Tel = %s WHERE CV_id = %s",
                           (Name, age, Email,Phone, id))
            mysql.connection.commit()
            cursor.close()
            flash('General info was updated successfully', 'success')
            return redirect('/cvs/{}'.format(id))
        else:
            flash('Only Admin has right to edit posts', 'danger')
            return redirect(url_for('index'))
    cursor = mysql.connection.cursor()
    result_value = cursor.execute("SELECT * FROM general WHERE CV_id = {}".format(id))
    if result_value > 0:
        entry = cursor.fetchone()
        edit_form = {}
        edit_form['FirstLastName'] = entry['FirstLastName']
        edit_form['age'] = entry['age']
        edit_form['email'] = entry['email']
        edit_form['Tel'] = entry['Tel']
        return render_template('edit-general.html', edit_form=edit_form)

@app.route('/edit-details/<int:id>',methods=['GET','POST'])
def edit_details(id):
    if request.method=='POST':
        cursor = mysql.connection.cursor()
        Education = request.form['Education']
        Experience = request.form['Experience']
        Skills = request.form['Skills']
        Additional_information = request.form['Additional_information']
        FL_name = session['FL_name']
        define_admin = cursor.execute("SELECT * FROM users WHERE Admin = 1 and FL_name = %s", ([FL_name]))
        if define_admin:
            cursor.execute("UPDATE detailed SET Education =%s, Experience = %s, Skills = %s, Additional_information = %s WHERE CV_id = %s",
                       (Education, Experience, Skills,Additional_information, id))
            mysql.connection.commit()
            cursor.close()
            flash('Addoitional info was updated successfully', 'success')
            return redirect(url_for('/cvs/{}'.format(id)))
        else:
            flash('Only Admin has right to edit posts', 'danger')
            return redirect(url_for('index'))
    cursor = mysql.connection.cursor()
    result_value = cursor.execute("SELECT * FROM detailed WHERE CV_id = {}".format(id))
    if result_value > 0:
        entry = cursor.fetchone()
        edit_form = {}
        edit_form['Education'] = entry['Education']
        edit_form['Experience'] = entry['Experience']
        edit_form['Skills'] = entry['Skills']
        edit_form['Additional_information'] = entry['Additional_information']
        return render_template('edit-details.html', edit_form=edit_form)

@app.route('/delete-entry/<int:id>')
def delete_post(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM detailed WHERE CV_id ={}".format(id))
    mysql.connection.commit()
    FL_name = session['FL_name']
    define_admin = cursor.execute("SELECT * FROM users WHERE Admin = 1 and FL_name = %s", ([FL_name]))
    if define_admin:
        cursor.execute("DELETE FROM general WHERE CV_id ={}".format(id))
        mysql.connection.commit()
        flash("Your entry has been deleted","success")
        cursor = mysql.connection.cursor()
        result_value = cursor.execute("SELECT * FROM general")
        if result_value > 0:
            entries = cursor.fetchall()
            cursor.close()
            return render_template('index.html', entries=entries)
    else:
        flash('Only Admin has right to delete posts', 'danger')
        return redirect(url_for('index'))

def allowed_file(filename):
    return '.' in filename \
           and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/edit-photo/<int:id>', methods=['GET', 'POST'])
def upload_file(id):
    #return render_template('photo.html')
    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        FL_name = session['FL_name']
        define_admin = cursor.execute("SELECT * FROM users WHERE Admin = 1 and FL_name = %s", ([FL_name]))
        if define_admin:
            # check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part','danger')
                return render_template('index.html')
            file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                flash('No selected file','danger')
                return render_template('photo.html',id=id)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = str(id) + '.' + filename.rsplit('.', 1)[1].lower()
                cursor = mysql.connection.cursor()
                try:
                    cursor.execute(
                        "INSERT INTO files(Filename, CV_id) VALUES (%s, %s)", (filename,id))
                    mysql.connection.commit()
                    cursor.close()
                except:
                    pass
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                flash('Success','success')
                redirect("/cvs/<int:id>")

        else:
            flash('Only Admin has right to upload fotos', 'danger')
            return redirect(url_for('index'))
    return render_template('photo.html',id=id)

@app.route('/logout/')
def logout():
    session.clear()
    flash('You have been logged out','info')
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True,port=5000)