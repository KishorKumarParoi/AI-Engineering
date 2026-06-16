import datetime

def greet_user():
    name = input("Enter your name: ")
    hour = datetime.datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    print(f"{greeting}, {name}! Welcome, and hi from your friendly Python script!")

greet_user()
