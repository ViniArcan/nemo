from getpass import getpass
from app import app, db, User 

with app.app_context():
    print("--- Create a New User ---")
    email = input("Enter user's Email: ")
    name = input("Enter user's Name: ")
    password = getpass(prompt="Enter user's Password: ")

    if not name.strip():
        name = "user"
        print("Name was empty, setting to 'user'.")

    # Check if user already exists
    if User.query.filter_by(email=email).first():
        print(f"Error: User with email '{email}' already exists.")
    else:
        new_user = User(email=email, password=password, name=name)
        db.session.add(new_user)
        db.session.commit()
        print(f"User '{name}' with email '{email}' was added successfully.")