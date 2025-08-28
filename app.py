from flask import Flask, render_template, request, redirect, url_for, session, send_file, Response
import io
import pymysql as p

app = Flask(__name__)

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "tiger",
    "db": "CHARLIE",
}

db_connection_pool = []

def create_db_connection():
    return p.connect(**db_config, autocommit=True)

def get_db_connection():
    if len(db_connection_pool) == 0:
        return create_db_connection()
    else:
        return db_connection_pool.pop()

def return_db_connection(connection):
    db_connection_pool.append(connection)

app.secret_key = 'FJJE'


def login_check(username, password):
    db_conn = get_db_connection()
    c = db_conn.cursor()
    c.execute('SELECT * FROM USERS WHERE USERNAME = %s AND PASSWORD = %s', (username, password))
    result = c.fetchone()
    c.close()
    return_db_connection(db_conn)
    if result:
        return True
    else:
        return False
    
    
def send_friend_request(username1, username2):
    db_conn = get_db_connection()
    c = db_conn.cursor()
    c.execute('SELECT MAX(ID) FROM FRIENDSHIPS')
    result = c.fetchone()
    new_id = result[0] + 1 if result[0] else 1
    try:
        c.execute('INSERT INTO FRIENDSHIPS VALUES (%s, %s, %s, %s)',(new_id, username1, username2, 'pending'))
        c.execute("COMMIT")
    except p.Error as e:
        c.execute('ROLLBACK')
        print(str(e))
    c.close()
    return_db_connection(db_conn)


def user_check(username):
    db_conn = get_db_connection()
    c = db_conn.cursor()
    c.execute('SELECT * FROM USERS WHERE USERNAME = %s', (username,))
    result = c.fetchone()
    c.close()
    return_db_connection(db_conn)
    if result:
        return True
    else:
        return False
        
def new_user(username, password, name, dob, contact, pic):
    db_conn = get_db_connection()
    c = db_conn.cursor()
    c.execute('SELECT MAX(USER_ID) FROM USERS')
    result = c.fetchone()
    user_id = result[0] + 1 if result[0] else 1
    try:
        c.execute('INSERT INTO USERS (USER_ID, USERNAME, PASSWORD, NAME, DOB, CONTACT, PIC) VALUES (%s, %s, %s, %s, %s, %s, %s)',(user_id, username, password, name, dob, contact, pic))
        c.close()
        return_db_connection(db_conn)
        return False
    except p.Error as e:
        print(str(e))
        return str(e)

def update_user(user_to_change, username='', password='', name='', dob='', contact='', about=''):
    try:
        db_conn = get_db_connection()
        c = db_conn.cursor()
        query = 'UPDATE USERS SET '

        values = []

        if username != '':
            query += 'USERNAME = %s, '
            values.append(username)
        if password != '':
            query += 'PASSWORD = %s, '
            values.append(password)
        if name != '':
            query += 'NAME = %s, '
            values.append(name)
        if dob != '':
            query += 'DOB = %s, '
            values.append(dob)
        if contact != '':
            query += 'CONTACT = %s, '
            values.append(contact)
        if about != '':
            query += 'ABOUT = %s, '
            values.append(about)

        # Remove the trailing comma and add the WHERE clause
        query = query.rstrip(', ')
        query += ' WHERE USERNAME = %s'

        # Add the last value for the WHERE clause
        values.append(user_to_change)

        # Execute the dynamic query
        c.execute(query, tuple(values))
        c.close()
        return_db_connection(db_conn)
    except p.Error as e:
        print(str(e))

def pending_requests(username):
    db_conn = get_db_connection()
    c = db_conn.cursor()
    c.execute('SELECT COUNT(*) FROM FRIENDSHIPS WHERE USERNAME2 = %s AND STATUS = %s', (username, 'pending'))
    result = c.fetchone()
    c.execute('SELECT USERNAME1 FROM FRIENDSHIPS WHERE USERNAME2=%s AND STATUS=%s',(username, 'pending'))
    pending_users = c.fetchall()
    c.close()
    return_db_connection(db_conn)
    return result, pending_users

def accepted_requests(username):
    db_conn = get_db_connection()
    c = db_conn.cursor()
    c.execute('SELECT COUNT(*) FROM FRIENDSHIPS WHERE (USERNAME1 = %s OR USERNAME2 = %s) AND STATUS = %s', (username, username, 'accepted'))
    result = c.fetchone()
    c.execute('SELECT CASE WHEN USERNAME1 = %s THEN USERNAME2 ELSE USERNAME1 END AS selected_username FROM FRIENDSHIPS WHERE STATUS = %s AND (USERNAME1 = %s OR USERNAME2 = %s)', (username, 'accepted', username, username))
    accepted_users = c.fetchall()
    c.close()
    return_db_connection(db_conn)
    return result, accepted_users

def add_post(image, description, username):
    db_conn = get_db_connection()
    c = db_conn.cursor()
    c.execute('SELECT MAX(POST_ID) FROM POSTS')
    result = c.fetchone()
    new_id = result[0] + 1 if result[0] else 1
    try:
        c.execute('INSERT INTO POSTS VALUES(%s, %s, %s, %s)', (new_id, image, description, username))
        c.execute('COMMIT')
        c.close()
        return_db_connection(db_conn)
    except p.Error as e:
        print(str(e))

def friend_posts(username):
    db_conn = get_db_connection()
    c = db_conn.cursor()
    trash, friends = accepted_requests(username)
    
    friends_tuple = tuple(friends)

    query = 'SELECT POST_ID, USERNAME, DESCRIPTION FROM POSTS WHERE USERNAME IN %s ORDER BY POST_ID DESC'
    c.execute(query, (friends_tuple,))

    posts = c.fetchall()
    c.close()
    return_db_connection(db_conn)
    print(posts)
    return posts

    

try:
     db_conn = get_db_connection()
     c = db_conn.cursor()
     c.execute('CREATE TABLE USERS(USER_ID INT PRIMARY KEY, USERNAME VARCHAR(15), PASSWORD VARCHAR(10), NAME VARCHAR(20), DOB DATE, CONTACT VARCHAR(10), ABOUT VARCHAR(50)  DEFAULT "My Bio", PIC LONGBLOB)')
     c.close()
     return_db_connection(db_conn)
except p.Error as e:
    print(str(e))

try: 
    db_conn = get_db_connection()
    c = db_conn.cursor()
    c.execute('CREATE TABLE POSTS(POST_ID INT PRIMARY KEY, IMAGE LONGBLOB, DESCRIPTION VARCHAR(50), USERNAME VARCHAR(15))')
    c.close()
    return_db_connection(db_conn)
except p.Error as e:
    print(str(e))

try:
    db_conn = get_db_connection()
    c = db_conn.cursor()
    c.execute("CREATE TABLE FRIENDSHIPS (ID INT PRIMARY KEY, USERNAME1 VARCHAR(15), USERNAME2 VARCHAR(15), STATUS ENUM('pending', 'accepted', 'rejected'))")
    c.close()
    return_db_connection(db_conn)
except p.Error as e:
    print(str(e))

@app.route('/')
def homepage():
    username = session.get('username')
    if not username:
        posts = None
    else:
        try:
            posts = friend_posts(username)
        except:
            posts = None
    return render_template('homepage.html', username=username, posts = posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user_exists = login_check(username, password)
        
        if user_exists:
            session['username'] = username
            return redirect(url_for('homepage'))
        else:
            return 'Login failed. Invalid username or password.'
    loginnotice = session.pop('login_notice', None)
    return render_template('login.html', loginnotice = loginnotice)

@app.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        contact_number = request.form['contact_number']
        dob = request.form['dob']
        name = request.form['name']
        image = request.files['image'].read()
        user_exists = user_check(username)
        if user_exists:
            return render_template('signup.html', user_check=user_check)
        user_created = new_user(username, password, name, dob, contact_number, image)
        if user_created:
            return user_created
        else:
            session['login_notice'] = '// Account created successfully, please log-in'
            return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/user/<string:username>', methods=['GET','POST'])
def user_profile(username):
    db_conn = get_db_connection()
    c = db_conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        about = request.form['about']
        update_user(user_to_change=session.get('username'), name=name, about=about)
    
    c.execute('SELECT * FROM USERS WHERE USERNAME = %s',(username,))
    user_set = c.fetchone()
    username = session.get('username')
    if user_set:
        c.execute('SELECT STATUS FROM FRIENDSHIPS WHERE (USERNAME1=%s AND USERNAME2=%s) OR (USERNAME1=%s AND USERNAME2=%s)',(username, user_set[1], user_set[1], username))
        friendship_status = c.fetchone()
        no_of_pending, pending_users = pending_requests(username)
        naccepted, ausers = accepted_requests(username)
        c.execute('SELECT * FROM POSTS WHERE USERNAME = %s ORDER BY POST_ID DESC',(user_set[1],))
        posts = c.fetchall()
        c.close()
        return_db_connection(db_conn)
        return render_template('user.html', user_set=user_set, username=username, fstatus = friendship_status, npending = no_of_pending, pusers = pending_users, naccepted=naccepted, ausers = ausers, posts=posts)
    else:
        return "User not found", 404

@app.route('/user/<string:username>/add-friend', methods=['GET','POST'])
def add_friend(username):
    db_conn = get_db_connection()
    c = db_conn.cursor()
    if request.method == 'POST':
        search_query = request.form['query']
        c.execute("SELECT USERNAME, NAME, ABOUT FROM USERS WHERE NAME LIKE %s OR USERNAME LIKE %s", ('%' + search_query + '%', '%' + search_query + '%'))
        results = c.fetchall()
        c.close()
        return_db_connection(db_conn)
        return render_template('add_friend.html', results=results, username=username)
    return render_template('add_friend.html', username=username)

@app.route('/user/<string:username1>/add-friend/<string:username2>', methods=['GET','POST'])
def add_friend_direct(username1, username2):
        send_friend_request(username1, username2)
        return redirect(url_for('user_profile', username=username2))

@app.route('/user/<string:username1>/accept-request/<string:username2>',methods=['POST','GET'])
def accept_request(username1, username2):
    db_conn = get_db_connection()
    c = db_conn.cursor()
    try:    
        c.execute('UPDATE FRIENDSHIPS SET STATUS = %s WHERE USERNAME1=%s AND USERNAME2=%s',('accepted',username2,username1))
        c.execute('COMMIT')
        print('Success')
    except p.Error as e:
        c.execute('ROLLBACK')
        print(str(e))
    c.close()
    return_db_connection(db_conn)
    return redirect(url_for('user_profile', username=username1))

@app.route("/user/<string:username>/new-post",methods=['POST','GET'])
def new_post(username):
    username = session.get('username')
    if request.method == 'POST':
        image = request.files['image'].read()
        description = request.form['description']
        add_post(image, description, username)
        return redirect(url_for('user_profile', username=username))
        
    return render_template('new_post.html',username=username)

@app.route('/get_image/<int:image_id>')
def get_image(image_id):
    db_conn = get_db_connection()
    c = db_conn.cursor()
    c.execute("SELECT IMAGE FROM POSTS WHERE POST_ID = %s", (image_id,))
    image_data = c.fetchone()[0]
    c.close()
    return_db_connection(db_conn)
    response = Response(io.BytesIO(image_data), content_type='image/jpeg')
    return response

@app.route('/log-out',methods=['GET'])
def logout():
    session.pop('username')
    return redirect(url_for('homepage'))

if __name__ == "__main__":
    app.run(debug=True, port=5000, host='0.0.0.0')