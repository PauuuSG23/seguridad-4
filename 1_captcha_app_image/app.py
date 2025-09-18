from flask import Flask, render_template, request, session, redirect, url_for, send_file # importaciones para crear la app y manejar las peticiones
from PIL import Image, ImageDraw, ImageFont # importaciones para crear la imagen del captcha y dibujar el texto junto con el fondo 
import random # importación para generar números aleatorios
import io # importación para manejar la imagen en memoria
import os # importación para generar una clave secreta aleatoria para la sesión y manejar rutas de archivos

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_answer = request.form.get('captcha')
        real_answer = session.get('captcha_answer')

        if user_answer and real_answer and user_answer.strip() == str(real_answer):
            return '<h2 style="color:green;"> CAPTCHA correcto. ¡Bienvenido!</h2><a href="/">Volver</a>'
        else:
            return '<h2 style="color:red;"> CAPTCHA incorrecto. Inténtalo de nuevo.</h2><a href="/">Volver</a>'

    return render_template('index.html')

@app.route('/captcha_image')
def captcha_image():
    num1 = random.randint(1, 9)
    num2 = random.randint(1, 9)
    operator = random.choice(['+', '-'])

    if operator == '+':
        answer = num1 + num2
    else:
        answer = num1 - num2

    session['captcha_answer'] = answer
    captcha_text = f"{num1} {operator} {num2} = ?"

    # Crear imagen
    img = Image.new('RGB', (150, 50), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except:
        font = ImageFont.load_default()

    draw.text((20, 10), captcha_text, font=font, fill=(0, 0, 0))

    # Guardar imagen en memoria
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
