from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, date
import uuid

app = Flask(__name__)
app.secret_key = 'clave_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/gestor_procesos'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Solicitud(db.Model):
    __tablename__ = 'solicitudes'
    id_solicitud = db.Column(db.String(36), primary_key=True)
    folio = db.Column(db.String(50))
    descripcion = db.Column(db.Text)
    tipo_area = db.Column(db.String(100))
    responsable_seguimiento = db.Column(db.String(100))
    fecha_creacion = db.Column(db.Date)
    fecha_estimacion = db.Column(db.Date)
    estatus = db.Column(db.String(50))
    fecha_aprobacion = db.Column(db.Date)
    aprobado_por = db.Column(db.String(100))
    retroalimentacion = db.Column(db.Text)
    fecha_limite_evaluacion = db.Column(db.Date)
    prioridad = db.Column(db.String(50))

    def agregar(self):
        db.session.add(self)
        db.session.commit()

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
    alta = ['urgente', 'auditoría', 'cumplimiento', 'crítico', 'inmediato']
    media = ['mejora', 'propuesta', 'ajuste']
    descripcion = descripcion.lower()
    if any(palabra in descripcion for palabra in alta):
        return 'Alta'
    elif any(palabra in descripcion for palabra in media):
        return 'Media'
    else:
        return 'Baja'

def dias_habiles_entre(fecha_inicio, fecha_fin):
    dias = 0
    while fecha_inicio < fecha_fin:
        if fecha_inicio.weekday() < 5:
            dias += 1
        fecha_inicio += timedelta(days=1)
    return dias

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
    nueva.fecha_creacion = datetime.now().date()
    nueva.fecha_estimacion = request.form.get('fecha_estimacion')
    nueva.fecha_estimacion = datetime.strptime(nueva.fecha_estimacion, '%Y-%m-%d').date() if nueva.fecha_estimacion else None
    nueva.estatus = 'pendiente'
    nueva.fecha_limite_evaluacion = nueva.fecha_creacion
    nueva.prioridad = detectar_prioridad(nueva.descripcion)
    nueva.agregar()
    return redirect(url_for('gestion_solicitudes'))

@app.route('/gestionSolicitudes')
def gestion_solicitudes():
    solicitudes = Solicitud.query.order_by(Solicitud.fecha_creacion.desc()).all()
    hoy = date.today()

    for solicitud in solicitudes:
        if solicitud.estatus == 'pendiente' and solicitud.fecha_creacion:
            dias = dias_habiles_entre(solicitud.fecha_creacion, hoy)
            if dias > 3:
                solicitud.estatus = 'Pendiente Evaluación'

    db.session.commit()
    return render_template('gestion_solicitudes.html', solicitudes=solicitudes)

@app.route('/actualizarSolicitud', methods=['POST'])
def actualizar_solicitud():
    solicitudes = Solicitud.query.all()
    for solicitud in solicitudes:
        sid = solicitud.id_solicitud
        accion = request.form.get('accion')

        if accion == f'aprobar_{sid}' or accion == f'rechazar_{sid}' or accion == f'finalizar_{sid}':
            solicitud.retroalimentacion = request.form.get(f'retroalimentacion_{sid}')
            fecha_aprobacion = request.form.get(f'fecha_aprobacion_{sid}')
            solicitud.fecha_aprobacion = datetime.strptime(fecha_aprobacion, '%Y-%m-%d') if fecha_aprobacion else None

            if f'aprobar_{sid}' == accion:
                solicitud.estatus = 'aprobada'
                solicitud.aprobado_por = request.form.get(f'aprobado_por_{sid}')
            elif f'rechazar_{sid}' == accion:
                solicitud.estatus = 'rechazada'
                solicitud.aprobado_por = 'rechazado'
            elif f'finalizar_{sid}' == accion:
                if solicitud.estatus == 'aprobada' and solicitud.aprobado_por and solicitud.aprobado_por.lower() not in ['rechazado', '']:
                    solicitud.estatus = 'finalizada'
                else:
                    flash(f'La solicitud con folio {solicitud.folio} no puede finalizarse sin aprobación válida.')

    db.session.commit()
    return redirect(url_for('gestion_solicitudes'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
