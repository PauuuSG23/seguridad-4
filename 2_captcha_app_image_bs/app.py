from flask import Flask, render_template, request, session, send_file
from PIL import Image, ImageDraw, ImageFont
import random
import io
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/', methods=['GET', 'POST'])
def index():
    status = None
    message = None

    if request.method == 'POST':
        user_answer = request.form.get('captcha')
        real_answer = session.get('captcha_answer')

        if user_answer and real_answer and user_answer.strip() == str(real_answer):
            status = "success"
            message = "CAPTCHA correcto. ¡Bienvenido!"
        else:
            status = "danger"
            message = "CAPTCHA incorrecto. Inténtalo de nuevo."

    # cache_buster para forzar recarga de la imagen
    cache_buster = int(datetime.utcnow().timestamp())
    return render_template('index.html', status=status, message=message, cache_buster=cache_buster)

@app.route('/captcha_image')
def captcha_image():
    num1 = random.randint(1, 9)
    num2 = random.randint(1, 9)
    operator = random.choice(['+', '-'])

    answer = num1 + num2 if operator == '+' else num1 - num2

    session['captcha_answer'] = answer
    captcha_text = f"{num1} {operator} {num2} = ?"

    # Crear imagen
    img = Image.new('RGB', (180, 60), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except:
        font = ImageFont.load_default()

    # Un poco de “ruido” leve para evitar OCR trivial (opcional)
    for _ in range(15):
        x1, y1 = random.randint(0, 180), random.randint(0, 60)
        x2, y2 = x1 + random.randint(-8, 8), y1 + random.randint(-8, 8)
        draw.line((x1, y1, x2, y2), fill=(220, 220, 220), width=1)

    draw.text((20, 15), captcha_text, font=font, fill=(0, 0, 0))

    # Guardar imagen en memoria
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8087)
