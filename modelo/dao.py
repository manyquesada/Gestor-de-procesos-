from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Text, DateTime, Integer
db = SQLAlchemy()


class Solicitud(db.Model):
    __tablename__ = 'solicitudes'
    id_solicitud = Column(String(36), primary_key=True)
    folio = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    tipo_area = Column(String(50))
    responsable_seguimiento = Column(String(150))
    fecha_creacion = Column(DateTime)
    fecha_estimacion = Column(DateTime)
    estatus = Column(String(50))
    fecha_aprobacion = Column(DateTime)
    aprobado_por = Column(String(150))
    retroalimentacion = Column(Text)
    fecha_limite_evaluacion = Column(DateTime)
    prioridad = Column(String(50))

    def agregar(self):
        db.session.add(self)
        db.session.commit()

    def actualizar(self):
        db.session.merge(self)
        db.session.commit()

    def eliminar(self):
        db.session.delete(self)
        db.session.commit()

    def consultaGeneral(self):
        return self.query.all()

    def consultaIndividual(self, id):
        return Solicitud.query.get(id)


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
    id_documento = Column(String(36), primary_key=True)
    nombre_archivo = Column(String(255))
    ruta_archivo = Column(Text)
    tipo_contenido = Column(String(100))
    tamano_archivo = Column(Integer)
    fecha_subida = Column(DateTime)
    id_proceso = Column(String(36))

    def agregar(self):
        db.session.add(self)
        db.session.commit()
