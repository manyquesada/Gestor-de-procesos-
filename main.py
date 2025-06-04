import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secreto'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/gestor_procesos'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'documentos')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

class Solicitud(db.Model):
    __tablename__ = 'solicitudes'
    id_solicitud = db.Column(db.String(36), primary_key=True)
    folio = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    tipo_area = db.Column(db.String(100))
    responsable_seguimiento = db.Column(db.String(100))
    fecha_creacion = db.Column(db.DateTime)
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

class Proceso(db.Model):
    __tablename__ = 'procesos'
    id_proceso = db.Column(db.String(36), primary_key=True)
    nombre = db.Column(db.String(150))
    descripcion = db.Column(db.Text)
    id_solicitud = db.Column(db.String(36), db.ForeignKey('solicitudes.id_solicitud'))
    fecha_registro = db.Column(db.DateTime)
    estatus_proceso = db.Column(db.String(50))

    solicitud = db.relationship("Solicitud", backref="procesos")

class DocumentoAdjunto(db.Model):
    __tablename__ = 'documentos_adjuntos'
    id_documento = db.Column(db.String(36), primary_key=True)
    nombre_archivo = db.Column(db.String(255))
    ruta_archivo = db.Column(db.Text)
    tipo_contenido = db.Column(db.String(100))
    tamano_archivo = db.Column(db.Integer)
    fecha_subida = db.Column(db.DateTime)
    id_proceso = db.Column(db.String(36), db.ForeignKey('procesos.id_proceso'))

    proceso = db.relationship("Proceso", backref="documentos")


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
    claves_alta = ['urgente', 'crítico', 'cumplimiento', 'auditoría']
    claves_media = ['mejora', 'optimización']
    for palabra in claves_alta:
        if palabra.lower() in descripcion.lower():
            return 'Alta'
    for palabra in claves_media:
        if palabra.lower() in descripcion.lower():
            return 'Media'
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
    nueva.fecha_creacion = datetime.now()
    nueva.fecha_estimacion = datetime.strptime(request.form['fecha_estimacion'], '%Y-%m-%d') if request.form['fecha_estimacion'] else None
    nueva.estatus = 'pendiente'
    nueva.fecha_limite_evaluacion = nueva.fecha_creacion.date() + timedelta(days=3)
    nueva.prioridad = detectar_prioridad(nueva.descripcion)
    nueva.agregar()
    return redirect(url_for('gestion_solicitudes'))

@app.route('/gestionSolicitudes')
def gestion_solicitudes():
    solicitudes = Solicitud.query.order_by(Solicitud.fecha_creacion.desc()).all()
    hoy = datetime.now().date()
    for solicitud in solicitudes:
        if solicitud.estatus == 'pendiente' and solicitud.fecha_creacion:
            dias = dias_habiles_entre(solicitud.fecha_creacion.date(), hoy)
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
            if 'rechazar' in accion:
                solicitud.estatus = 'rechazada'
                solicitud.aprobado_por = 'rechazado'
            elif 'aprobar' in accion:
                solicitud.estatus = 'aprobada'
                solicitud.aprobado_por = request.form.get(f'aprobado_por_{sid}')
                solicitud.retroalimentacion = request.form.get(f'retroalimentacion_{sid}')
                fecha_aprobacion = request.form.get(f'fecha_aprobacion_{sid}')
                solicitud.fecha_aprobacion = datetime.strptime(fecha_aprobacion, '%Y-%m-%d') if fecha_aprobacion else None
            elif 'finalizar' in accion:
                if solicitud.estatus == 'aprobada' and solicitud.aprobado_por and solicitud.aprobado_por.lower() != 'rechazado':
                    solicitud.estatus = 'finalizada'
                else:
                    flash(f'La solicitud {solicitud.folio} no puede finalizarse sin aprobación válida.')
    db.session.commit()
    return redirect(url_for('gestion_solicitudes'))

@app.route('/generarProceso/<id_solicitud>')
def generar_proceso(id_solicitud):
    solicitud = Solicitud.query.get(id_solicitud)
    if solicitud and solicitud.estatus == 'aprobada':
        existente = Proceso.query.filter_by(id_solicitud=id_solicitud).first()
        if not existente:
            nuevo = Proceso(
                id_proceso=str(uuid.uuid4()),
                nombre=f"Proceso para {solicitud.folio}",
                descripcion=solicitud.descripcion,
                id_solicitud=solicitud.id_solicitud,
                fecha_registro=datetime.now(),
                estatus_proceso='en seguimiento'
            )
            db.session.add(nuevo)
            db.session.commit()
            flash("Proceso generado exitosamente.")
        else:
            flash("Este proceso ya fue generado previamente.")
    else:
        flash("Solo puede generar procesos a partir de solicitudes aprobadas.")
    return redirect(url_for('gestion_solicitudes'))

@app.route('/gestionProcesos')
def gestion_procesos():
    procesos = Proceso.query.join(Solicitud).filter(Solicitud.estatus == 'aprobada').all()
    return render_template('gestion_procesos.html', procesos=procesos)

@app.route('/procesos/<id_proceso>/documentos', methods=['GET', 'POST'])
def documentos(id_proceso):
    proceso = Proceso.query.get_or_404(id_proceso)
    if request.method == 'POST':
        archivo = request.files['archivo']
        if archivo:
            nombre_archivo = secure_filename(archivo.filename)
            ruta = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)
            archivo.save(ruta)
            doc = DocumentoAdjunto(
                id_documento=str(uuid.uuid4()),
                nombre_archivo=nombre_archivo,
                ruta_archivo=ruta,
                tipo_contenido=archivo.content_type,
                tamano_archivo=os.path.getsize(ruta),
                fecha_subida=datetime.now(),
                id_proceso=proceso.id_proceso
            )
            db.session.add(doc)
            db.session.commit()
            flash('Documento subido correctamente')
            return redirect(url_for('documentos', id_proceso=id_proceso))

    archivos = [doc.nombre_archivo for doc in proceso.documentos]
    return render_template('documentos.html', proceso=proceso, archivos=archivos)

@app.route('/descargar/<nombre_archivo>')
def descargar_documento(nombre_archivo):
    return send_from_directory(app.config['UPLOAD_FOLDER'], nombre_archivo, as_attachment=True)

@app.route('/ver_documento/<nombre_archivo>')
def ver_documento(nombre_archivo):
    return send_from_directory(app.config['UPLOAD_FOLDER'], nombre_archivo)


if __name__ == '__main__':
    app.run(debug=True)
