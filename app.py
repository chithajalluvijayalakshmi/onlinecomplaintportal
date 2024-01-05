from flask import Flask,url_for,session,redirect,render_template,request,flash,send_file,send_from_directory
from flask_session import Session 
from flask_mysqldb import MySQL
from key import *
from itsdangerous import URLSafeTimedSerializer
from stoken import token
from cmail import *
import os
from otp import genotp
from flask import abort

app = Flask(__name__)
app.secret_key = secret_key
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

app.secret_key = '23efgbnjuytr'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'online'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)
@app.route('/',methods=['GET','POST'])
def home():
     if request.method=="POST":
        name=request.form['name']
        emailid=request.form['emailid']
        message=request.form['message']
        cursor=mysql.connection.cursor()
        cursor.execute('insert into contactus(name,emailid,message) values(%s,%s,%s)',[name,emailid,message])
        mysql.connection.commit()
     return render_template('home.html')


@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        print(request.form)
        username=request.form['name']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT count(*) as h from user where username=%s and password=%s',[username,password])
        count=cursor.fetchone()
        print(count['h'])
        if count['h']==1:
            session['user']=username
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
            return render_template('login.html')

    return render_template('login.html')

@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    default_adminid = 1
    default_password = 'admin'  # Change this to your actual default password

    if request.method == 'POST':
        adminid = request.form['adminid']
        password = request.form['password']

        if adminid == str(default_adminid) and password == default_password:
            session['admin'] = adminid
            return redirect(url_for('admindashboard'))
        else:
            flash('Invalid username or password')
            return render_template('adminlogin.html')

    return render_template('adminlogin.html')

    
# @app.route('/adminregister', methods=['GET', 'POST'])
# def adminregister():
#     if request.method == 'POST':
#         adminid=request.form['adminid']
#         password = request.form['password']
#         email = request.form['email']
#         phno = request.form['phonenumber']
#         cursor = mysql.connection.cursor()
#         cursor.execute('insert into admin values(%s,%s,%s,%s)',[adminid,email,phno,password])
#         mysql.connection.commit()
#         cursor.close()
#         return redirect(url_for('adminlogin'))
#     return render_template('adminregister.html')


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        mobile = request.form['phno']
        state = request.form['state']
        address = request.form['address']
        pincode = request.form['pincode']
        cursor = mysql.connection.cursor()
        # cursor.execute('select count(*) from user where username=%s', [username])
        # count = cursor.fetchone()
        # print(count)
        cursor.execute('select count(*) from user where email=%s', [email])
        count1 = cursor.fetchone()
        print(count1)
        cursor.close()
        # if count==1:
        #     flash('username already in use')
        #     return render_template('registration.html')
        if count1==1:
            flash('Email already in use')
            return render_template('registration.html')

        data = {'username': username, 'email': email, 'password': password, 'phno': mobile, 'state': state,
                'address': address, 'pincode': pincode}
        subject = 'Email Confirmation'
        body = f"Thanks for signing up\n\nfollow this link for further steps-{url_for('confirm', token=token(data, salt), _external=True)}"
        sendmail(to=email, subject=subject, body=body)
        flash('Confirmation link sent to email')
        return redirect(url_for('login'))
    return render_template('registration.html')

@app.route('/confirm/<token>')
def confirm(token):
    try:
        # Verify the token
        serializer = URLSafeTimedSerializer(secret_key)
        data = serializer.loads(token, salt=salt, max_age=180)
    except Exception as e:
        abort (404,'Link Expired register again')
    else:
        cursor = mysql.connection.cursor()
        email=data['email']

        # Check if the user is already registered
        cursor.execute('SELECT COUNT(*) FROM user WHERE email = %s', [email])
        count = cursor.fetchone()

        if count==1:
            cursor.close()
            flash('You are already registerterd!')
            return redirect(url_for('login'))
        else:
            cursor.execute('INSERT INTO user (username, email, password, phno, state, address, pincode) VALUES (%s, %s, %s, %s, %s, %s, %s)', [data['username'], data['email'], data['password'], data['phno'], data['state'], data['address'], data['pincode']])
            mysql.connection.commit()
            print('hi')
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('login'))


        

@app.route('/forgot',methods=['GET','POST'])
def forgot():
    if request.method=='POST':
        email=request.form['email']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from user where email=%s',[email])
        count=cursor.fetchone()
        cursor.close()
        count=count['count(*)']
        if count == 1:
            cursor=mysql.connection.cursor()
            cursor.execute('SELECT email from user where email=%s',[email])
            status=cursor.fetchone()
            cursor.close()
            subject='Forget Password'
            confirm_link=url_for('reset',token=token(email,salt=salt2),_external=True)
            body=f"Use this link to reset your password-\n\n{confirm_link}"
            sendmail(to=email,body=body,subject=subject)
            flash('Reset link sent check your email')
            return redirect(url_for('login'))
        else:
            flash('Invalid email id')
            return render_template('forgot.html')
    return render_template('forgot.html')


@app.route('/reset/<token>',methods=['GET','POST'])
def reset(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        email=serializer.loads(token,salt=salt2,max_age=180)
    except:
        abort(404,'Link Expired')
    else:
        if request.method=='POST':
            newpassword=request.form['npassword']
            confirmpassword=request.form['cpassword']
            if newpassword==confirmpassword:
                cursor=mysql.connection.cursor()
                cursor.execute('update user set password=%s where email=%s',[newpassword,email])
                mysql.connection.commit()
                flash('Reset Successful')
                return redirect(url_for('login'))
            else:
                flash('Passwords mismatched')
                return render_template('newpassword.html')
        return render_template('newpassword.html')

@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        flash('User Successfully logged out')
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
@app.route('/adminlogout')
def adminlogout():
    if session.get('admin'):
        session.pop('admin')
        flash(' Admin Successfully logged out')        
        return redirect(url_for('adminlogin'))
    else:
        return redirect(url_for('adminlogin'))
    

@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if session.get('user'):
        
        if request.method == "POST":
            id1=genotp()
            email = request.form['email']
            problem = request.form['problem']
            address=request.form['address']
            image=request.files['image']
            categorie=request.form['categorie']
            cursor=mysql.connection.cursor()
            filename=id1+'.jpg'
            data=cursor.execute('select * from complaint')
            print(data)
            cursor.execute('INSERT INTO complaint (id,username,email,problem,address,categorie) VALUES (%s,%s,%s,%s,%s,%s)',[id1,session.get('user'),email,problem,address,categorie]) 
            mysql.connection.commit()
            cursor.close()
            path=r"C:\Users\India\Desktop\onlinecomplain\static"
            image.save(os.path.join(path,filename))
            
            subject = 'complaint deatils'
            body = 'complaint are submitted' 
            sendmail(email,subject,body)
            flash('complaint submitted')
            return redirect(url_for('home'))
        return render_template('complaintform.html')
    else:
        return redirect(url_for('login'))



        
@app.route('/admindashboard')
def admindashboard():
    if session.get('admin'):
        cursor=mysql.connection.cursor()
        cursor.execute('select * from complaint')
        details = cursor.fetchall()
        return render_template('admindashboard.html',details=details)
    else:
        return redirect(url_for('alogin'))
@app.route('/notsolved')
def notsolved():
    if session.get('admin'):
        cursor=mysql.connection.cursor()
        cursor.execute('select * from complaint where status="Not Started"')
        details=cursor.fetchall()
        print(details)
        '''if request.method=="POST":
            id1=request.form['id1']
            status=request.form['status']
            cursor.execute('update complaint set status=%s where id=%s',[id1,status])
            cursor.commit()'''
        return render_template('unsolved.html',details=details)
    else:
        return redirect(url_for('alogin'))
@app.route('/update/<id1>',methods=['GET','POST'])
def update(id1):
    if session.get('admin'):
        cursor=mysql.connection.cursor()
        cursor.execute('select * from complaint where id=%s',[id1])
        data=cursor.fetchone()
        cursor.close()
        if request.method=='POST':
            status=request.form['status']
            cursor=mysql.connection.cursor()
            cursor.execute('update complaint set status=%s where id=%s',[status,id1])
            mysql.connection.commit()
            cursor.execute('select email from complaint where id=%s',[id1])
            
            email=cursor.fetchone()
            print(email)
            cursor.close()
            subject = 'complaint deatils'#--------------------
            body = f'the status of the complaint {status}' #-----------------------------
            sendmail(email['email'],subject,body)#-----------------
            flash('updated successfully')
            cursor.close()
            flash('updated successfully')
            return redirect(url_for('notsolved'))
     
    else:
        return redirect(url_for('alogin'))
    return render_template('update.html',data=data)
@app.route('/currently')
def currently():
    if session.get('admin'):
        cursor=mysql.connection.cursor()
        cursor.execute('select * from complaint where status="In Progress"')
        details=cursor.fetchall()
        print(details)
        return render_template('inprogress.html',details=details)
    else:
        return redirect(url_for('alogin'))
@app.route('/oldcomplaint')
def oldcomplaint():
    if session.get('admin'):
        cursor=mysql.connection.cursor()
        cursor.execute('select * from complaint where status="resolved"')
        details=cursor.fetchall()
        return render_template('inprogress.html',details=details)
    else:
        return redirect(url_for('alogin'))
@app.route('/user')
def user():
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select * from complaint where username=%s',[session.get('user')])
        details=cursor.fetchall()
        print(details)
        return render_template('userstatus.html',details=details)

@app.route('/view/<id1>')
def view(id1):
        path=os.path.dirname(os.path.abspath(__file__))
        static_path=os.path.join(path,'static')
        return send_from_directory(static_path,f'{id1}.jpg')
@app.route('/viewcontactus')
def contactusview():
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select * from contactus order by date desc')
        data=cursor.fetchall()
        print(data)
        return render_template('viewcontactus.html',data=data)
    else:
        return redirect(url_for('login'))


app.run(use_reloader=True,debug=True)

