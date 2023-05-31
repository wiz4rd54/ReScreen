from flask import Flask
from flask import session,redirect,request, render_template, send_from_directory
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
import resparser
import os
import fitz 
from docx2pdf import convert

app = Flask(__name__,template_folder="templates")
app.config['SECRET_KEY'] = "s3cur3s3cr3tk3y"
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'rescreen'
app.config['UPLOAD_FOLDER'] = "D:\\bhagirath\\College\\minor\\final\\upload"
ALLOWED_EXTENSIONS = ['pdf','docx','doc','txt']
mysql = MySQL(app)

@app.route('/')
def main_page():
    return render_template("index.html")

@app.route('/login',methods=["POST"])
def login():
    session['username'] = request.form['email']
    email = request.form['email']
    password = request.form['password']
    
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM user WHERE email=%s"
    cursor.execute(query,(email,))
    data = cursor.fetchall()
    cursor.close()
    if password==data[0][-1]:
        user_id = int(data[0][0])
        return redirect(f"/dashboard/{user_id}")

@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username', None)
        return redirect("/#login")
    else:
        return '<p> User already logged out </p>'

@app.route('/signup',methods=["POST"])
def signup():
    username = request.form['name']
    email = request.form['email']
    password = request.form['password']
    confirm = request.form['confirmpassword']

    if confirm==password:
        cursor = mysql.connection.cursor()
        cursor.execute('''INSERT INTO user VALUES(user_id,%s,%s,%s)''',(username,email,password))
        mysql.connection.commit()
        
        query = "SELECT * FROM user WHERE email=%s"
        cursor.execute(query,(email,))
        data = cursor.fetchall()
        user_id = int(data[0][0])

        session['username'] = email
        cursor.close()
        return redirect(f"/dashboard/{user_id}")

@app.route('/dashboard/<int:user_id>')
def dashboard(user_id):
    if 'username' in session:
        query = f"SELECT * FROM user WHERE user_id={user_id}"
        cursor = mysql.connection.cursor()
        cursor.execute(query)
        data = cursor.fetchall()[0]

        query = f"SELECT * FROM categories where user_id={user_id}"
        cursor.execute(query)
        categories = cursor.fetchall()
        listCategories=[]
        for i in categories:
            listCategories.append({'category_id':i[0],'category_name':i[1],'skills':i[2],'education':i[3],'experience':i[4],'user_id':i[5]})
        
        cursor.close()
        user_data = {'user_id':data[0],'name':data[1]} 
        return render_template("dashboard.html", user_data = user_data, categories_data = listCategories)

@app.route('/userprofile/<int:user_id>')
def userprofile(user_id):
    query = f"SELECT * FROM user WHERE user_id={user_id}"
    cursor = mysql.connection.cursor()
    cursor.execute(query)
    data = cursor.fetchall()[0]
    cursor.close()
    user_data = {'user_id':data[0],'name':data[1],'email':data[2]} 
    return render_template("userprofile.html", user_data = user_data)

@app.route('/newcategory/<int:user_id>', methods=['POST'])
def newcategory(user_id):
    name = request.form['name']
    cursor = mysql.connection.cursor()
    cursor.execute('''INSERT INTO categories VALUES(category_id,%s,skills,education,experience,%s)''',(name,user_id))
    mysql.connection.commit()
    cursor.close()
    return redirect(f"/dashboard/{user_id}")

@app.route('/deletecategory/<int:user_id>/<int:category_id>')
def deletecategory(user_id,category_id):
    cursor = mysql.connection.cursor()
    query = f"DELETE FROM categories WHERE category_id={category_id}"
    cursor.execute(query)
    mysql.connection.commit()
    cursor.close()
    return redirect(f"/dashboard/{user_id}")

@app.route('/category/<int:user_id>/<int:category_id>')
def category(user_id,category_id):
    cursor = mysql.connection.cursor()
    query = f"SELECT * FROM user WHERE user_id={user_id}"
    cursor = mysql.connection.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    user_data = []
    for i in data[0]:
        user_data.append(i)

    query = f"SELECT * FROM categories WHERE category_id={category_id}"
    cursor.execute(query)
    categoryData = cursor.fetchall()
    categories_data = []
    for i in categoryData[0]:
        categories_data.append(i)
    if categories_data[-2]:
        work_experience_split = categories_data[-2].split('-')
        categories_data.pop(-2)
        categories_data.append(int(work_experience_split[0]))
        categories_data.append(int(work_experience_split[1]))

    query = f"SELECT * FROM applicants WHERE category_id={category_id}"
    cursor.execute(query)
    applicantsData = cursor.fetchall()
    cursor.close()

    applicantsData = sorted(applicantsData, key=lambda x: x[8],reverse=True)

    return render_template("category.html",category_data=categories_data,user_data=user_data,applicants_data=applicantsData)

@app.route('/updatedescription/<int:user_id>/<int:category_id>', methods=["POST"])
def updatedescription(user_id,category_id):

    cursor = mysql.connection.cursor()
    query = f"SELECT * FROM categories WHERE category_id={category_id}"
    cursor = mysql.connection.cursor()
    cursor.execute(query)
    data = cursor.fetchall()[0]
    cursor.close()

    skills = request.form['skills']
    work_experience_minimum = request.form['experience_minimum']
    work_experience_maximum = request.form['experience_maximum']
    work_experience = work_experience_minimum+"-"+work_experience_maximum
    education = request.form['education']

    cursor = mysql.connection.cursor()
    cursor.execute('''UPDATE categories SET skills = %s, education = %s, experience = %s WHERE category_id=%s''',(skills,education,work_experience,category_id))
    cursor.execute(query)
    mysql.connection.commit()
    cursor.close()
    return redirect(f"/category/{user_id}/{category_id}")

@app.route('/open_file/<int:file_id>')
def open_file(file_id):
    filename = str(file_id)+".pdf"
    #file_path = os.path.join(app.config['UPLOAD_FOLDER'],filename)
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploadresume/<int:user_id>/<int:category_id>',methods=["POST"])
def upload_file(user_id,category_id):
    if request.method == 'POST':
        files = request.files.getlist('file')
        for file in files:
            if allowed_file(file.filename):
                cursor = mysql.connection.cursor()
                cursor.execute('''INSERT INTO applicants VALUES(applicant_id,name,contact,email,links,skills,education,experience,final_score,%s,%s)''',(user_id,category_id))
                mysql.connection.commit()   
                applicant_id = cursor.lastrowid
                cursor.close()
                path = ""
                if file.filename.rsplit('.', 1)[1].lower() == 'docx' or file.filename.rsplit('.', 1)[1].lower() == 'doc':
                    try:
                        file.filename = str(applicant_id)+'.docx'
                        filename = secure_filename(file.filename)
                        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        convert(path)
                        file.filename = str(applicant_id)+'.pdf'
                        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    except AssertionError:
                        pass
                else:
                    file.filename = str(applicant_id)+'.pdf'
                    filename = secure_filename(file.filename)
                    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                file.filename = str(applicant_id)+'.pdf'
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                with fitz.open(path) as doc:
                    resumeText = ""
                    for page in doc:
                        resumeText += page.get_text()

                query = f"SELECT * FROM categories WHERE category_id={category_id}"
                cursor = mysql.connection.cursor()
                cursor.execute(query)
                categories_data = list(cursor.fetchall()[0])
                cursor.close()
                categories_data[2] = categories_data[2].split(" ")
                work_experience_split = categories_data[-2].split('-')
                minimum = (int(work_experience_split[0]))
                maximum = (int(work_experience_split[1]))
                
                name,phone,email,links,skills_score,education_score,workexperience_score,total_score = '',0,'','',0,0,0,0
                name = resparser.extract_names(resumeText)
                phone = resparser.extract_phone_numbers(resumeText)
                email = resparser.extract_email_addresses(resumeText)[0]
                links = ','.join(resparser.extract_links(resumeText))
                skills_score = resparser.extract_skills(resumeText,categories_data[2])
                education_score = resparser.extract_education(resumeText,categories_data[3])
                workexperience_score = resparser.extract_workexperience(resumeText,minimum,maximum)
                total_score = round(skills_score + education_score + workexperience_score,2)
                print(name,phone,email,links,skills_score,education_score,workexperience_score,total_score)
                
                cursor = mysql.connection.cursor()
                cursor.execute('''UPDATE applicants SET name = %s, contact = %s, email = %s, links = %s, skills = %s, education = %s, experience = %s, final_score = %s  WHERE applicant_id=%s''',(name,phone,email,links,skills_score,education_score,workexperience_score,total_score,applicant_id))
                cursor.execute(query)
                mysql.connection.commit()
                cursor.close()
                
            
        return redirect(f"/category/{user_id}/{category_id}")
if __name__ == '__main__':
    app.run(host='localhost',port=8080, debug=True)