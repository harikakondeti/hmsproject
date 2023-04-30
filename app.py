from flask import Flask,flash,redirect,render_template,url_for,request,session
from flask_session import Session
from flask_mysqldb import MySQL
from otp import genotp
from cmail import sendmail
import random
import os
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from tokenreset import token
from io import BytesIO
from datetime import date
from datetime import datetime
import smtplib
app=Flask(__name__)
app.secret_key='*67@hjyjhk'
app.config['SESSION_TYPE']='filesystem'
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='Admin'
app.config['MYSQL_DB']='hms'
Session(app)
mysql=MySQL(app)
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/adminregister', methods=["GET","POST"])
def registration():
    if request.method=="POST":
        userid=request.form.get('userid')
        username=request.form.get('username')
        password=request.form.get('password')
        email=request.form.get('email')
        passcode=request.form.get('passcode')
        #define college code
        code='sdmsmk$#23'
        if code==passcode:
            cursor=mysql.connection.cursor()
            cursor.execute('SELECT email from admin')
            edata=cursor.fetchall()
            #print(data)
            cursor.close()
            otp=genotp()
            subject='Thanks for registering to the application'
            body=f'Use this otp to register {otp}'
            sendmail(email,subject,body)
            return render_template('otp.html',otp=otp,userid=userid,username=username,password=password,email=email)
        else:
            flash('Invalid college code')
        #return redirect(url_for('otp'))
    return render_template('Registration.html')
@app.route('/otp/<otp>/<userid>/<username>/<password>/<email>',methods=['GET','POST'])
def otp(otp,userid,username,password,email):
    if request.method=='POST':
        uotp=request.form['otp']
        if otp==uotp:
            cursor=mysql.connection.cursor()
            cursor.execute('insert into admin values(%s,%s,%s,%s)',(userid,username,password,email))
            mysql.connection.commit()
            cursor.close()
            flash('Details registered')
            return redirect(url_for('login'))
        else:
            flash('Wrong otp')
            return render_template('otp.html',otp=otp,userid=userid,username=username,password=password,email=email)
@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('Adminpage'))
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT count(*) from admin where username=%s and password=%s',[username,password])
        count=cursor.fetchone()[0]
        print(count)
        if count==0:
            flash('Invalid username or password')
            return render_template('Admin-login.html')
        else:
            session['user']=username
            return redirect(url_for('Adminpage'))
    return render_template('Admin-login.html')
@app.route('/adminpage',methods=['GET','POST'])
def Adminpage():
    if session.get('user'):
        return render_template('adminhomepage.html')
@app.route('/addstudent',methods=['GET','POST'])
def addstudent():
    if session.get('user'):
        if request.method=='POST':
            id1=request.form['id1']
            name=request.form['name']
            section=request.form['section']
            room=request.form['roomno']
            mobile=request.form['mobileno']
            cursor=mysql.connection.cursor()
            cursor.execute('insert into students(Id,Name,Section,roomno,mobile) values(%s,%s,%s,%s,%s)',[id1,name,section,room,mobile])
            mysql.connection.commit()
            cursor.close()
            return redirect(url_for('studentrecord'))
        return render_template('Add-student.html')
@app.route('/studentrecord',methods=['GET','POST'])
def studentrecord():
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT * from students')
        data=cursor.fetchall()
        cursor.close()
        
        return render_template('Student Record.html',data=data)
@app.route('/delete/<id>')
def delete(id):
    cursor=mysql.connection.cursor()
    cursor.execute('delete from students where id=%s',[id])
    mysql.connection.commit()
    cursor.close()
    flash('student delete successfully')
    return redirect(url_for('studentrecord'))
@app.route('/update/<id>',methods=['GET','POST'])
def update(id):
    cursor=mysql.connection.cursor()
    cursor.execute('select * from students where id=%s',[id])
    data=cursor.fetchone()
    if request.method=='POST':
        id1=request.form['id']
        name=request.form['name']
        room =request.form['Room']
        mobile=request.form['mobile']
        section=request.form['section']
        cursor.execute('update students set Name=%s,roomno=%s,mobile=%s,section=%s where id=%s',[name,room,mobile,section,id])
        mysql.connection.commit()
        return redirect(url_for('studentrecord'))
    return render_template('update.html',data=data)
@app.route('/checkin',methods=['GET','POST'])
def checkin():
    if session.get('user'):
        details=None
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT * from students')
        data=cursor.fetchall()
        data1=request.args.get('name') if request.args.get('name') else 'empty'
        print(data1)
        cursor.execute('SELECT * from students where id=%s',[data1])
        details=cursor.fetchone()
        cursor.execute('SELECT date,id,name,roomno,section,mobile,checkin,checkout from records')
        std_records=cursor.fetchall()
        cursor.close()
        if request.method=='POST':
            cursor=mysql.connection.cursor()
            Id=request.form['empCode']
            today=date.today()
            day=today.day
            month=today.month
            year=today.year
            today_date=datetime.strptime(f'{year}-{month}-{day}','%Y-%m-%d')
            date_today=datetime.strftime(today_date,'%Y-%m-%d')
            Name=request.form['name']
            section=request.form['section']
            roomno=request.form['roomno']
            mobileno=request.form['mobileno']
            cursor.execute('select count(*) from records where Id=%s and date=%s',[Id,date_today])
            count=int(cursor.fetchone()[0])
            if Id=="" or Name=="" or section=="" or roomno=="" or mobileno=="":
                flash('Select The student Id first')
            elif count>=1:
                flash('The student already gone outside')
            else:
                cursor=mysql.connection.cursor()
                cursor.execute('insert into records(Id,Name,section,roomno,mobile,checkin,checkout,date) values(%s,%s,%s,%s,%s,%s,%s,%s)',[Id,Name,section,roomno,mobileno,None,None,date_today])
                mysql.connection.commit()
                cursor.execute('SELECT date,Id,Name,section,roomno,mobile,checkin,checkout from records')
                std_records=cursor.fetchall()
                cursor.close()
        return render_template('Check in-page.html',data1=data1,data=data,details=details,std_records=std_records)
@app.route('/checkoutupdate/<date>/<id1>')
def checkoutupdate(date,id1):
    cursor=mysql.connection.cursor()
    cursor.execute('update records set checkout=current_timestamp() where date=%s and Id=%s',[date,id1])
    mysql.connection.commit()
    return redirect(url_for('checkin'))
@app.route('/checkinupdate/<date>/<id1>')
def checkinupdate(date,id1):
    cursor=mysql.connection.cursor()
    cursor.execute('update records set checkin=current_timestamp() where date=%s and Id=%s',[date,id1])
    mysql.connection.commit()
    return redirect(url_for('checkin'))
@app.route('/visitorcheckin',methods=['GET','POST'])
def visitorcheckin():
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT * from students')
        data=cursor.fetchall()
        cursor.execute('SELECT * from visitorrecords')
        details=cursor.fetchall()
        if request.method=='POST':
            sid=request.form['sid']
            today=date.today()
            day=today.day
            month=today.month
            year=today.year
            today_date=datetime.strptime(f'{year}-{month}-{day}','%Y-%m-%d')
            date_today=datetime.strftime(today_date,'%Y-%m-%d')
            sid=request.form['sid']
            visitorname=request.form['visitorname']
            visitormobile=request.form['visitormobile']
            mysql.connection.commit()
            cursor.execute('insert into visitorrecords(id,visitorname,visitormobile,date) values(%s,%s,%s,%s)',[sid,visitorname,visitormobile,date_today])
            mysql.connection.commit()
            cursor.execute('SELECT * from visitorrecords')
            details=cursor.fetchall()
        return render_template('visitorcheckin.html',data=data,details=details)
@app.route('/Checkoutupdate/<vid>')
def Checkoutupdate(vid):
    cursor=mysql.connection.cursor()
    cursor.execute('update visitorrecords set checkout=current_timestamp() where vid=%s',[vid])
    mysql.connection.commit()
    return redirect(url_for('visitorcheckin'))
@app.route('/Checkinupdate/<vid>')
def Checkinupdate(vid):
    cursor=mysql.connection.cursor()
    cursor.execute('update visitorrecords set checkin=current_timestamp() where vid=%s',[vid])
    mysql.connection.commit()
    return redirect(url_for('visitorcheckin'))
@app.route('/forgotpassword',methods=['GET','POST'])
def forgot():
    if request.method=='POST':
        username=request.form['username']
        cursor=mysql.connection.cursor()
        cursor.execute('select username from admin')
        data=cursor.fetchall()
        if (username,) in data:
            cursor.execute('select email from admin where username=%s',[username])
            data=cursor.fetchone()[0]
            cursor.close()
            subject=f'Reset Password for {data}'
            body=f'Reset the password using-{request.host+url_for("newpassword",token=token(username,360))}'
            sendmail(data,subject,body)
            flash('Reset link sent to your mail')
            return redirect(url_for('login'))
        else:
            return 'Invalid user id'
    return render_template('forgot.html')
@app.route('/newpassword/<token>',methods=['GET','POST'])
def newpassword(token):
    try:
        s=Serializer(app.config['SECRET_KEY'])
        username=s.loads(token)['user']
        if request.method=='POST':
            npass=request.form['npassword']
            cpass=request.form['cpassword']
            if npass==cpass:
                cursor=mysql.connection.cursor()
                cursor.execute('update admin set password=%s where username=%s',[npass,username])
                mysql.connection.commit()
                return 'Password reset Successfull'
            else:
                return 'Password mismatch'
        return render_template('newpassword.html')
    except:
        return 'Link expired try again'
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('login'))
    else:
        flash('already logged out!')
        return redirect(url_for('login'))
app.run(debug=True)                                                                                         

        

    

