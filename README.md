# Exam-Generator
## Instructions

In order to run this program, you need to have [python(3.7+)](https://www.python.org/downloads/) and [pip](https://pypi.org/project/pip/) installed. 

Additionally you need to have the pip packages [django(3.0+)](https://pypi.org/project/Django/) and [psycopg2(2.8.4+)](https://pypi.org/project/psycopg2/) installed. 

Our database is a PostgreSQL 12 server, you can download it [here](https://www.postgresql.org/). 
For adminstration reasons we are using pgadmin4 which you can find [here](https://www.pgadmin.org/). 
As we run LaTeX commands, LaTeX needs to be installed (e.g. [MiKTeX](https://miktex.org/download)).

*  `pip install django`
*  `pip install psycopg2`
*  [PostgreSQL 12](https://www.postgresql.org/)
*  [pgadmin4](https://www.pgadmin.org/)
*  [MiKTeX](https://miktex.org/download)

For a quick setup, you can consider [the virtual machine](https://drive.google.com/open?id=1dzR7wIdqRTVSNmqeew-3XJlNIQ2IB3Vc). (User: sim, Password: admin)  It runs Ubuntu and has all needed dependencies installed. 
To start the server, run following commands: 
`cd Documents/project10/ExamGenerator`  
`python3 manage.py runserver`  
Now you can browse to `localhost:8000`. If you want to log in as an admin, log in with username = admin and password = admin .

## Setting up the database

In the settings.py file you can find the Database Configuration. 

```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'database_name',
        'USER': 'username',
        'PASSWORD': 'password',
        'HOST': '127.0.0.1',
        'PORT': '5432'
    }
}
```

The attributes need to match the pgadmin4 database declarations.


## Testing
1.  Setup: <br>
    install selenium : `pip install selenium` <br>
2.  Run all tests: <br>
    `manage.py test` <br>
    
    Run a specific test: <br>
    `manage.py test ExamGeneratorApp.tests.[name of test]` <br>
    
3.  Coverage: <br>
    Setup : `pip install coverage`<br>
    Create overage report : `coverage run --source='.' manage.py test `<br>
    Read coverage report in terminal : `coverage report`
    
    For further details you can create a seperate coverage report for every single python file. It will be in html-format. <br>
    1. `coverage html`
    2. the command created a folder "ExamGenerator/htmlcov" in which there is a coverage report for every single python file.
    
    To delete the old coverage file run : `coverage erase`
    



    
