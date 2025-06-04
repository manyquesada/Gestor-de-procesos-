from flask import Flask, render_template, request, redirect, url_for
from modelo.dao import db, Solicitud
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/gestor_procesos'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registroSolicitud')
def registro_solicitud():
    return render_template('registro_solicitud.html')

@app.route('/registrarSolicitud', methods=['POST'])
def registrar_solicitud():
    nueva = Solicitud()
    nueva.id_solicitud = str(uuid.uuid4())
    nueva.folio = generar_folio()
    nueva.descripcion = request.form['descripcion']
    nueva.tipo_area = request.form['tipo_area']
    nueva.responsable_seguimiento = request.form['responsable_seguimiento']
    nueva.fecha_creacion = datetime.now()
    nueva.fecha_estimacion = datetime.strptime(request.form['fecha_estimacion'], '%Y-%m-%d') if request.form['fecha_estimacion'] else None
    nueva.estatus = 'pendiente'
    nueva.fecha_limite_evaluacion = nueva.fecha_creacion
    nueva.prioridad = detectar_prioridad(nueva.descripcion)
    nueva.agregar()
    return redirect(url_for('gestion_solicitudes'))

@app.route('/gestionSolicitudes')
def gestion_solicitudes():
    solicitudes = Solicitud.query.order_by(Solicitud.fecha_creacion.desc()).all()
    return render_template('gestion_solicitudes.html', solicitudes=solicitudes)

@app.route('/actualizarSolicitud', methods=['POST'])
def actualizar_solicitud():
    solicitudes = Solicitud.query.all()
    for solicitud in solicitudes:
        sid = solicitud.id_solicitud
        accion = request.form.get('accion')

        if accion == f'aprobar_{sid}' or accion == f'rechazar_{sid}':
            solicitud.aprobado_por = request.form.get(f'aprobado_por_{sid}')
            solicitud.retroalimentacion = request.form.get(f'retroalimentacion_{sid}')
            fecha_aprobacion = request.form.get(f'fecha_aprobacion_{sid}')
            solicitud.fecha_aprobacion = datetime.strptime(fecha_aprobacion, '%Y-%m-%d') if fecha_aprobacion else None
            solicitud.estatus = 'aprobada' if 'aprobar' in accion else 'rechazada'
    db.session.commit()
    return redirect(url_for('gestion_solicitudes'))

def generar_folio():
    ult = Solicitud.query.order_by(Solicitud.folio.desc()).first()
    num = 1
    if ult and ult.folio and ult.folio.startswith('CCADPRC-'):
        try:
            num = int(ult.folio.split('-')[-1]) + 1
        except:
            pass
    return f'CCADPRC-{num:04d}'

def detectar_prioridad(descripcion):
    claves = ['urgente', 'auditoría', 'cumplimiento']
    for palabra in claves:
        if palabra.lower() in descripcion.lower():
            return 'Alta'
    return 'Media'

if __name__ == '__main__':
    app.run(debug=True)