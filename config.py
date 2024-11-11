import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://root:3C8qrbjt51iS4uvKOa1mjU8U9kz5S7ds@dpg-csp2bve8ii6s73a502q0-a.frankfurt-postgres.render.com/flrcd'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
