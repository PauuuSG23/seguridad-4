from flask import Flask, render_template, request, session, send_file, flash, redirect, url_for, make_response
from PIL import Image, ImageDraw, ImageFont
import random, io, os, re, math
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# -------------------------
# Helpers, los helpers se usan en varias vistas
# -------------------------
def _only_digits(text: str) -> str:
    import re as _re
    return _re.sub(r'\\D+', '', text or '')

def _no_cache_response(html):
    """Devuelve una respuesta HTML con cabeceras no-cache para evitar páginas en el historial."""
    resp = make_response(html)
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

# -------------------------
# Home (menú)
# -------------------------
@app.route('/home')
def home():
    return _no_cache_response(render_template('home.html'))

# -------------------------
# CAPTCHA aritmético (ÚNICA RUTA PRINCIPAL)
# -------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_answer = request.form.get('captcha')
        real_answer = session.get('captcha_answer')

        if user_answer and real_answer and user_answer.strip() == str(real_answer):
            session['just_logged_in'] = True
            flash("CAPTCHA correcto. ¡Bienvenido!", "success")
            return redirect(url_for('bienvenido'))
        else:
            flash("CAPTCHA incorrecto. Inténtalo de nuevo.", "danger")
            return redirect(url_for('index'))

    cache_buster = int(datetime.utcnow().timestamp())
    return _no_cache_response(render_template('index.html', cache_buster=cache_buster))

@app.route('/captcha_image')
def captcha_image():
    # Operaciones disponibles: división entera, potencia y factorial
    operator = random.choice(['//', '^', '!'])

    if operator == '//':  # División entera
        # Asegurar división exacta
        num2 = random.randint(2, 9)
        quotient = random.randint(1, 9)
        num1 = num2 * quotient  # num1 será múltiplo de num2
        answer = num1 // num2   # Esto será igual a quotient
        op_symbol = '÷'
        captcha_text = f"{num1} {op_symbol} {num2} = ?"
        
    elif operator == '^':  # Potencia
        # Definir AMBOS números para potencia
        num1 = random.randint(2, 5)  # Base pequeña
        num2 = random.randint(2, 3)  # Exponente pequeño
        answer = num1 ** num2
        op_symbol = '^'
        captcha_text = f"{num1}{op_symbol}{num2} = ?"
        
    else:  # Factorial '!'
        # Para factorial, solo necesitamos un número
        num1 = random.randint(3, 6)  # 3!=6, 4!=24, 5!=120, 6!=720
        answer = math.factorial(num1)
        op_symbol = '!'
        captcha_text = f"{num1}{op_symbol} = ?"

    session['captcha_answer'] = answer

    # Ajustar el ancho de la imagen según el contenido
    text_length = len(captcha_text)
    img_width = max(180, text_length * 15)  # Ancho dinámico
    
    img = Image.new('RGB', (img_width, 60), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except:
        font = ImageFont.load_default()

    # Añadir ruido de fondo
    for _ in range(15):
        x1, y1 = random.randint(0, img_width), random.randint(0, 60)
        x2, y2 = x1 + random.randint(-8, 8), y1 + random.randint(-8, 8)
        draw.line((x1, y1, x2, y2), fill=(220, 220, 220), width=1)

    # Centrar el texto
    text_x = (img_width - len(captcha_text) * 12) // 2
    draw.text((max(10, text_x), 15), captcha_text, font=font, fill=(0, 0, 0))

    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

# -------------------------
# CAPTCHA por identificación (2 pasos)
# -------------------------
@app.route('/captcha-id', methods=['GET', 'POST'])
def captcha_id_step1():
    if request.method == 'POST':
        user_id = _only_digits(request.form.get('identificacion'))

        if not user_id or len(user_id) < 6 or len(user_id) > 12:
            flash("La identificación debe tener entre 6 y 12 dígitos.", "danger")
            return redirect(url_for('captcha_id_step1'))

        session['user_id'] = user_id

        # Dos posiciones distintas 1-indexadas
        p1 = random.randint(1, len(user_id))
        p2 = random.randint(1, len(user_id))
        while p2 == p1:
            p2 = random.randint(1, len(user_id))
        session['id_positions'] = sorted([p1, p2])

        return redirect(url_for('captcha_id_step2'))

    return _no_cache_response(render_template('captcha_id_step1.html'))

@app.route('/captcha-id/verify', methods=['GET', 'POST'])
def captcha_id_step2():
    user_id = session.get('user_id')
    pos = session.get('id_positions')

    if not user_id or not pos:
        flash("Primero ingresa tu identificación.", "danger")
        return redirect(url_for('captcha_id_step1'))

    if request.method == 'POST':
        d1 = _only_digits(request.form.get('digit1'))
        d2 = _only_digits(request.form.get('digit2'))

        if len(d1) != 1 or len(d2) != 1:
            flash("Debes ingresar un dígito en cada campo.", "danger")
            return redirect(url_for('captcha_id_step2'))

        ok = (d1 == user_id[pos[0]-1]) and (d2 == user_id[pos[1]-1])

        if ok:
            session['just_logged_in'] = True
            flash("Verificación por identificación completada. ¡Bienvenido!", "success")
            # Limpiar datos sensibles
            session.pop('id_positions', None)
            return redirect(url_for('bienvenido'))
        else:
            flash("Los dígitos no coinciden. Inténtalo de nuevo.", "danger")
            # Reasignar nuevas posiciones
            p1 = random.randint(1, len(user_id))
            p2 = random.randint(1, len(user_id))
            while p2 == p1:
                p2 = random.randint(1, len(user_id))
            session['id_positions'] = sorted([p1, p2])
            return redirect(url_for('captcha_id_step2'))

    return _no_cache_response(render_template('captcha_id_step2.html', positions=pos))

# -------------------------
# Bienvenido
# -------------------------
@app.route('/bienvenido')
def bienvenido():
    # Solo mostrar si viene de un login/captcha recién completado
    if session.get('just_logged_in'):
        # Consumir la bandera para que al volver atrás NO se muestre de nuevo
        session.pop('just_logged_in', None)
        return _no_cache_response(render_template('welcome.html'))
    # Si intenta llegar sin pasar por verificación, lo mandamos al menú
    flash("Por favor, inicia desde el menú.", "danger")
    return redirect(url_for('home'))

# -------------------------
# Arranque
# -------------------------
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8090)