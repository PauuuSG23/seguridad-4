from flask import Flask, render_template, request, session, send_file, flash, redirect, url_for
from PIL import Image, ImageDraw, ImageFont
import random, io, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_answer = request.form.get('captcha')
        real_answer = session.get('captcha_answer')

        if user_answer and real_answer and user_answer.strip() == str(real_answer):
            flash("CAPTCHA correcto. ¡Bienvenido!", "success")
            return redirect(url_for('bienvenido'))
        else:
            flash("CAPTCHA incorrecto. Inténtalo de nuevo.", "danger")
            return redirect(url_for('index'))

    cache_buster = int(datetime.utcnow().timestamp())
    return render_template('index.html', cache_buster=cache_buster)

@app.route('/bienvenido')
def bienvenido():
    return render_template('welcome.html')

@app.route('/captcha_image')
def captcha_image():
    # Números pequeños para mantener cuentas rápidas (1–9)
    num1 = random.randint(1, 9)
    num2 = random.randint(1, 9)

    # Ahora permite suma, resta y multiplicación
    operator = random.choice(['+', '-', '*'])

    if operator == '+':
        answer = num1 + num2
        operator_symbol = '+'
    elif operator == '-':
        answer = num1 - num2
        operator_symbol = '−'   # guion medio estético 
    else:  # '*'
        answer = num1 * num2
        operator_symbol = '×'   # muestra el símbolo × en la imagen

    # Guarda la respuesta en sesión
    session['captcha_answer'] = answer

    # Texto a dibujar (usamos el símbolo visual, no afecta el cálculo)
    captcha_text = f"{num1} {operator_symbol} {num2} = ?"

    # Crear imagen
    img = Image.new('RGB', (180, 60), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except:
        font = ImageFont.load_default()

    # Ruido ligero
    for _ in range(15):
        x1, y1 = random.randint(0, 180), random.randint(0, 60)
        x2, y2 = x1 + random.randint(-8, 8), y1 + random.randint(-8, 8)
        draw.line((x1, y1, x2, y2), fill=(220, 220, 220), width=1)

    # Texto
    draw.text((20, 15), captcha_text, font=font, fill=(0, 0, 0))

    # Respuesta como PNG en memoria
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8088)
