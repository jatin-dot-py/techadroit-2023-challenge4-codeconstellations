from flask import Flask, request, render_template, session,redirect,url_for,escape
import hashlib
import uuid
from pymongo import MongoClient
from typing import List

app=Flask(__name__)
client = MongoClient('localhost', 27017)
main_db = client['hackathon-job-portal']
user_table=main_db['users']
comapny_table=main_db['companies']
activejobs_table=main_db['active_jobs']

app.secret_key = 'key@321'
#Checks for User Authentication
def is_authenticated(session):
    if session.get('loggedin')==True:
        return True
    return False


#Routes

@app.route('/home')
def home_nav_bar():
    if is_authenticated(session):
        return render_template('home-bar.html')
    else:
        return redirect(url_for('login'))
@app.route('/')
def index():
    return redirect(url_for('jobs'))

@app.route('/login',methods=["GET","POST"])
def login():
    session['loggedin']=False
    if request.method=="POST":
        email=request.form.get('email')
        password=request.form.get('password')

        if user_table.find_one({'email':email}):
            items =user_table.find_one({'email':email})
            if items['email']==email and items['password']==str(hashlib.sha256(password.encode()).hexdigest()):
                session['loggedin']=True
                session['email']=email
                return redirect(url_for('jobs'))
            else:
                return render_template("login.html",notification="Invalid Credentials!")
        else:
            return render_template("login.html",notification="An error has occured")
            

    else:
        return render_template('login.html')


@app.route('/register',methods=["GET","POST"])
def signup():
    if request.method=="POST":
        full_name=request.form.get('fullname')
        email=request.form.get('email')
        if user_table.find_one({'email':email}):
            return render_template("register.html",message="Email already in use!")
        password=request.form.get('password')
        confirm_password=request.form.get('confirm_password')
        userid= str(uuid.uuid1())
        mobile=""
        qualification=""
        skills=""
        experience=""
        hashed_password=str(hashlib.sha256(password.encode()).hexdigest())
        profile_photo="https://conferenceoeh.com/wp-content/uploads/profile-pic-dummy.png"

        user_table.insert_one({'uuid':userid,'password':hashed_password,'email':email,'name':full_name,"mobile":mobile,"qualification":qualification,"skills":skills,"experience":experience,'profile_photo':profile_photo})
        return render_template('register.html',message="Success! Please Continue to Login")

    return render_template("register.html")


@app.route('/jobs',methods=["GET","POST"])
def jobs():
    if is_authenticated(session):
        if request.method=="POST":
            if user_table.find_one({'email':session.get('email')}):
                data=user_table.find_one({'email':session.get('email')})
                if data['qualification']!="" and data['skills']!="" and data['mobile']!="":
                    pass
                else:
                    return render_template('profilecustomize.html')
            location=request.form.get('location')
            industry=request.form.get('industry')
            experience=request.form.get('experience')

            jobs=[]
            for items in activejobs_table.find():
                jobs.append(items)

            res=filter_jobs(jobs,industry,location)
            return render_template('job-res.html',message=res)

        return render_template('userhome.html')
    else:
        return redirect(url_for('login'))
    
@app.route('/companies')
def comapnies():
    if is_authenticated(session):
        company_data=[]
        for items in comapny_table.find():
            company_data.append(items)
        return render_template('companies.html',companies=company_data)
    else:
        return redirect(url_for('login'))
    

@app.route('/profile',methods=["GET","POST"])
def profile():
    if is_authenticated(session):
        if request.method=="POST":

            skill=request.form.get('skills')
            qualification=request.form.get('qualification')
            mobile=request.form.get('mobile')
            experience=request.form.get('experience')

            if len(mobile)>10:
                return render_template('profilecustomize.html',notification="Invalid Details")

            user_table.update_one({'email':session.get('email')},{ "$set": { 'mobile': request.form.get('mobile'),'experience':request.form.get('experience'),'qualification':request.form.get('qualifications'),'skills':request.form.get('skills') } })
        if user_table.find_one({'email':session.get('email')}):
            data=user_table.find_one({'email':session.get('email')})
            
            if len(data['mobile'])==0 and len(data['skills'])==0  and len(data['qualification']) ==0 and (data["experience"])=='':
                return render_template('profilecustomize.html')
        data=user_table.find_one({'email':session.get('email')})
        
            
        return render_template('profile.html',notification=data)
    
@app.route('/company-register',methods=["GET","POST"])
def comapny_register():
    if request.method=="POST":
        c_name=request.form.get('company_name')
        c_email=request.form.get('email')
        c_overview=request.form.get('overview')
        c_password=request.form.get('password')
        c_link=request.form.get('link')
        c_logo="https://spa-company.com/wp-content/uploads/2020/03/dummy-logo-08.png"

        comapny_table.insert_one({'name':c_name,'email':c_email,'overview':c_overview,'password':c_password,'link':c_link,'logo':c_logo})
        return "Registration Success! <a href='/company-login'>Please Login Here</a>"
    return render_template('company-register.html')
@app.route('/company-home')
def company_home():
    if session.get('company_login'):
        data=comapny_table.find_one({'email':session.get('email')})
        return render_template('company-home.html',message=data)
    else: 
        redirect(url_for('company-login'))

@app.route('/company-login',methods=["GET","POST"])
def company_login():
    if request.method=="POST":
        email=request.form.get('email')
        password=request.form.get('password')

        if comapny_table.find_one({'email':email}):
            data=comapny_table.find_one({'email':email})
            if data['password']==password and data['email']==email:
                session.clear()
                session['company_login']=True
                session['email']=email
                return redirect(url_for('company_home'))
            else:
                return "An Error has Occured, Please Contact your Administrator"
        else:
            return "An Error has Occured, Please Contact your Administrator"
    return render_template('company-login.html')



@app.route('/company-jobs',methods=["GET","POST"])
def company_jobs():
    if session.get('company_login'):
        if request.method=="POST":
            jobtitle=request.form.get('job_title')
            experience=request.form.get('experience')
            tags=request.form.get('tags')

            activejobs_table.insert_one({"title":jobtitle,"experience":experience,"tags":tags.split(",")})
            return render_template('company-jobs.html',message="Job added Successfully!")
        return render_template('company-jobs.html')
    else: 
        redirect(url_for('company-login'))
@app.route('/support')
def support():
    return render_template('support.html')
def filter_jobs(jobs: List[dict], industry: str, locations: List[str]) -> List[dict]:
    filtered_jobs = []

    for job in jobs:
        job_tags = job['tags']
        industry_match = False
        location_match = False

        for tag in job_tags:
            if tag == industry:
                industry_match = True
            if tag in locations:
                location_match = True

            if industry_match and location_match:
                filtered_jobs.append(job)
                break

    return filtered_jobs


app.run(debug=True,host='0.0.0.0')
