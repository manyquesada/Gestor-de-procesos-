from flask import Flask, render_template, request, redirect, url_for
from modelo.dao import db, Solicitud
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/gestor_procesos'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/solicitudes')
def mostrarSolicitudes():
    sol = Solicitud()
    solicitudes = sol.consultaGeneral()
    return render_template('Solicitudes.html', solicitudes=solicitudes)

@app.route('/registroSolicitud')
def registroSolicitud():
    return render_template('RegistroSolicitud.html')

@app.route('/guardarSolicitud', methods=['POST'])
def guardarSolicitud():
    nueva = Solicitud()
    nueva.id_solicitud = str(uuid.uuid4())
    nueva.descripcion = request.form['descripcion']
    nueva.tipo_area = request.form['tipo_area']
    nueva.responsable_seguimiento = request.form['responsable']
    nueva.fecha_creacion = datetime.now()
    nueva.estatus = 'Pendiente'
    nueva.folio = generar_folio()
    nueva.fecha_limite_evaluacion = nueva.fecha_creacion + timedelta(days=5)  # puedes ajustar a días hábiles si deseas
    nueva.agregar()
    return redirect(url_for('mostrarSolicitudes'))

def generar_folio():
    ult = Solicitud.query.order_by(Solicitud.folio.desc()).first()
    num = 1
    if ult:
        try:
            num = int(ult.folio.split('-')[-1]) + 1
        except:
            pass
    return f'CCADPRC-{num:04d}'

if __name__ == '__main__':
    app.run(debug=True)
