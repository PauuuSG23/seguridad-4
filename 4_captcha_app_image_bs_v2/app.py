from flask import Flask, render_template, request, session, send_file, flash, redirect, url_for, make_response
from PIL import Image, ImageDraw, ImageFont
import random, io, os, re, math
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# -------------------------
# Helpers
# -------------------------
def _only_digits(text: str) -> str:
    import re as _re
    return _re.sub(r'\D+', '', text or '')

def _factorial(n):
    """Calcula factorial de números pequeños para el captcha"""
    if n < 0 or n > 7:  # Limitar para no sobrecargar
        return 1
    return math.factorial(n) if n >= 0 else 1

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
# CAPTCHA aritmético MEJORADO
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
    # Cantidad de números (2, 3 o 4)
    num_count = random.choice([2, 3, 4])

    # Generar lista de números
    numbers = []
    for _ in range(num_count):
        if num_count == 2:
            numbers.append(random.randint(10, 99))  # si es simple, usar dos dígitos
        else:
            numbers.append(random.randint(1, 20))   # si es más largo, usar 1–20

    # Operadores permitidos
    operators = ['+', '-', '*', '//']

    # Construir expresión
    expression_parts = []
    for i, num in enumerate(numbers):
        expression_parts.append(str(num))
        if i < num_count - 1:
            expression_parts.append(random.choice(operators))

    expression = " ".join(expression_parts)

    # Calcular respuesta de forma segura
    try:
        if '//' in expression:
            # asegurar que los divisores no sean cero
            while ' // 0' in expression:
                expression = expression.replace(' // 0', f' // {random.randint(1,9)}')
        answer = eval(expression)
    except ZeroDivisionError:
        answer = 0

    session['captcha_answer'] = answer

    # Texto para mostrar (más bonito, con símbolos matemáticos)
    captcha_text = expression.replace('//', '÷').replace('*', '×')

    # Generar imagen
    img = Image.new('RGB', (320, 70), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except:
        font = ImageFont.load_default()

    # Líneas de fondo para dificultar OCR
    for _ in range(20):
        x1, y1 = random.randint(0, img.width), random.randint(0, img.height)
        x2, y2 = x1 + random.randint(-12, 12), y1 + random.randint(-12, 12)
        draw.line((x1, y1, x2, y2), fill=(200, 200, 200), width=1)

    # Dibujar texto
    draw.text((20, 20), f"{captcha_text} = ?", font=font, fill=(0, 0, 0))

    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

# -------------------------
# NUEVO CAPTCHA: Secuencia lógica
# -------------------------
@app.route('/captcha-logico', methods=['GET', 'POST'])
def captcha_logico():
    if request.method == 'POST':
        user_answer = request.form.get('logico_answer')
        real_pattern = session.get('logico_pattern')
        sequence_type = session.get('sequence_type')

        if user_answer and real_pattern:
            try:
                user_num = int(user_answer.strip())
                if user_num == real_pattern:
                    session['just_logged_in'] = True
                    flash("Secuencia lógica correcta. ¡Bienvenido!", "success")
                    return redirect(url_for('bienvenido'))
                else:
                    flash(f"Incorrecto. La secuencia era {sequence_type}. Inténtalo de nuevo.", "danger")
            except ValueError:
                flash("Por favor ingresa un número válido.", "danger")
        
        return redirect(url_for('captcha_logico'))

    # Generar nueva secuencia lógica
    sequence_type = random.choice(['par', 'impar', 'primo', 'fibonacci', 'multiplo'])
    
    if sequence_type == 'par':
        start = random.randint(2, 20) * 2  # Número par
        sequence = [start, start + 2, start + 4, "?"]
        answer = start + 6
    elif sequence_type == 'impar':
        start = random.randint(1, 19) 
        if start % 2 == 0: 
            start += 1  # Asegurar que sea impar
        sequence = [start, start + 2, start + 4, "?"]
        answer = start + 6
    elif sequence_type == 'primo':
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
        idx = random.randint(0, len(primes) - 4)
        sequence = [primes[idx], primes[idx+1], primes[idx+2], "?"]
        answer = primes[idx+3]
    elif sequence_type == 'fibonacci':
        a, b = random.randint(1, 5), random.randint(2, 8)
        sequence = [a, b, a+b, b+(a+b), "?"]
        answer = (a+b) + (b+(a+b))
    else:  # multiplo
        multiplier = random.randint(2, 5)
        start = random.randint(1, 10)
        sequence = [start*multiplier, (start+1)*multiplier, (start+2)*multiplier, "?"]
        answer = (start+3)*multiplier

    session['logico_pattern'] = answer
    session['sequence_type'] = sequence_type

    return _no_cache_response(render_template('captcha_logico.html', 
                                            sequence=sequence, 
                                            sequence_type=sequence_type))

# -------------------------
# CAPTCHA por identificación
# -------------------------
@app.route('/captcha-id', methods=['GET', 'POST'])
def captcha_id_step1():
    if request.method == 'POST':
        user_id = _only_digits(request.form.get('identificacion'))

        if not user_id or len(user_id) < 6 or len(user_id) > 12:
            flash("La identificación debe tener entre 6 y 12 dígitos.", "danger")
            return redirect(url_for('captcha_id_step1'))

        session['user_id'] = user_id

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
            session.pop('id_positions', None)
            return redirect(url_for('bienvenido'))
        else:
            flash("Los dígitos no coinciden. Inténtalo de nuevo.", "danger")
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
    if session.get('just_logged_in'):
        session.pop('just_logged_in', None)
        return _no_cache_response(render_template('welcome.html'))
    flash("Por favor, inicia desde el menú.", "danger")
    return redirect(url_for('home'))

# -------------------------
# Arranque
# -------------------------
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8090)
