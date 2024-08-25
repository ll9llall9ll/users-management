from flask import Flask, render_template, request, redirect, url_for, session
from murad_db import getUserByUsernameAndPassword, insertUser, getUserByUsername

class AppData:
    def __init__(self):
        self.IsLoggedIn = False
        self.loggedInusername = None

class User:
    def __init__(self, username, name, surname, password, is_admin=False):
        self.username = username
        self.name = name
        self.surname = surname
        self.password = password
        self.is_admin = is_admin  


    
    def change_password(self, new_password):
        self.password = new_password

def check_password(password: str) -> str:
    if len(password) < 8:
        return "Password is too short. It should be at least 8 characters long."
    
    has_number = False
    has_symbol = False
    special_characters = '.,:;!?}''()[]{<>+=-*%/$^|@#&_~`'

    for char in password:
        if char.isdigit():
            has_number = True
        if char in special_characters:
            has_symbol = True

    if not has_number:
        return "Password should contain at least one number."
    if not has_symbol:
        return "Password should contain at least one special character ('.,:;!?}''()[]{<>+=-*%/$^|@#&_~`')."
    
    return None 

app = Flask(__name__, static_folder='test')
appData = AppData()
app.secret_key = 'supersecretkey'

users_data = {
    'user1': User('user1', 'Ivan', 'Ivanov', 'password1'),
    'user2': User('user2', 'Hovannes', 'Hovhannisyan', 'password2'),
    'janedoe': User('janedoe', 'Jane', 'Doe', 'newsecurepassword' ),
    'admin': User('admin', 'Petr', 'Poghosyan', 'supersecret', True)  }

#users = {user.username: user.password for user in users_data.values()}

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/edit_user', methods = ['GET', 'POST'])
def edit_user():
    current_username = request.args.get('username')
    user_info = users_data[current_username]
    if request.method == 'GET' and appData.IsLoggedIn == True and users_data[appData.loggedInusername].is_admin == True and appData.IsLoggedIn:
        return render_template('user.html', user = user_info, username = current_username) 
    elif request.method == 'POST' and appData.IsLoggedIn == True and users_data[appData.loggedInusername].is_admin == True and appData.IsLoggedIn:
        users_data[current_username].name = request.form['name']
        users_data[current_username].surname = request.form['surname'] 
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        current_username = request.form['username']
        current_password = request.form['password']
        db_user = getUserByUsernameAndPassword(current_username, current_password)
        if db_user != None:
            appData.IsLoggedIn = True
            appData.loggedInusername = db_user.username
            return redirect(url_for('profile'))
        else:
            error = "Invalid username or password"
    elif appData.IsLoggedIn:
        return redirect(url_for('profile'))
    return render_template('login.html', error=error)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not appData.IsLoggedIn:
        return redirect(url_for('login'))
    user = users_data[appData.loggedInusername]
    if request.method == 'POST':
        user.name = request.form['name']
        user.surname = request.form['surname']

    return render_template('profile.html', username=user.username, name=user.name, surname=user.surname, is_admin=user.is_admin)

@app.route('/view_users',methods=['GET', 'POST'])
def view_users():
    if not appData.IsLoggedIn or not users_data[appData.loggedInusername].is_admin:
        return redirect(url_for('login'))

    return render_template('view_users.html', users=users_data)


@app.route('/admin_menu')
def admin_menu():
    if not appData.IsLoggedIn or not users_data[appData.loggedInusername].is_admin:
        return redirect(url_for('login'))
    
    return render_template('admin_menu.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    appData.IsLoggedIn = False
    appData.loggedInusername = None
    return redirect(url_for('login'))

@app.route('/changePassword', methods=['GET', 'POST'])
def changepassword():
    if not appData.IsLoggedIn:
        return redirect(url_for('login'))
    
    error = None
    if request.method == 'POST':
        new_password = request.form['password']
        error = check_password(new_password)
        if error is None:
            user = users_data[appData.loggedInusername]
            user.change_password(new_password)
            #users[appData.loggedInusername] = new_password  
            return redirect(url_for('profile'))
    return render_template('changepassword.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        current_username = request.form['new_username']
        password = request.form['new_password']
        repeat_password = request.form['repeat_password']
        
        if getUserByUsername(current_username) != None:
            error = "Username already exists, please choose a different username."
        elif password != repeat_password:
            error = "Passwords do not match. Please try again."
        else:
            error = check_password(password)
            if error is None:
                user = User(current_username, '', '', password)
                insertUser(user)
                return redirect(url_for('login'))
    return render_template('register.html', error=error)

@app.route('/delete_user', methods=['GET', 'POST'])
def delete_user(username):
    if username in users_data:
        del users_data[username]
        del users[username]
        return redirect(url_for('view_users'))
    else:
        return "User not found"


if __name__ == '__main__':
    app.run(debug=False)
