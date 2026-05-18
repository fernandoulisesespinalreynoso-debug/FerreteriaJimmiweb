"""
Ferretería Super Jimmy — Backend de Vacantes
Flask REST API simplificada
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vacantes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

import os
from flask import send_from_directory

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/vacantes')
def vacantes_page():
    return send_from_directory('.', 'vacantes.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)
# ── MODELOS ────────────────────────────────────────────────────────────────────

class Vacante(db.Model):
    __tablename__ = 'vacantes'
    id          = db.Column(db.Integer, primary_key=True)
    titulo      = db.Column(db.String(100), nullable=False)
    tipo        = db.Column(db.String(50), default='Tiempo completo')
    modalidad   = db.Column(db.String(50), default='Presencial')
    descripcion = db.Column(db.Text)
    activa      = db.Column(db.Boolean, default=True)
    creada_en   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'titulo': self.titulo,
            'tipo': self.tipo, 'modalidad': self.modalidad,
            'descripcion': self.descripcion, 'activa': self.activa,
            'creada_en': self.creada_en.isoformat(),
        }


class Aplicacion(db.Model):
    __tablename__ = 'aplicaciones'
    id         = db.Column(db.Integer, primary_key=True)
    vacante_id = db.Column(db.Integer, db.ForeignKey('vacantes.id'), nullable=False)
    nombre     = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(120), nullable=False)
    telefono   = db.Column(db.String(20))
    mensaje    = db.Column(db.Text)
    enviado_en = db.Column(db.DateTime, default=datetime.utcnow)
    vacante    = db.relationship('Vacante', backref='aplicaciones')

    def to_dict(self):
        return {
            'id': self.id, 'vacante_id': self.vacante_id,
            'vacante': self.vacante.titulo,
            'nombre': self.nombre, 'email': self.email,
            'telefono': self.telefono, 'mensaje': self.mensaje,
            'enviado_en': self.enviado_en.isoformat(),
        }


# ── RUTAS: VACANTES ────────────────────────────────────────────────────────────

@app.route('/api/vacantes', methods=['GET'])
def listar_vacantes():
    vacantes = Vacante.query.filter_by(activa=True).order_by(Vacante.creada_en.desc()).all()
    return jsonify([v.to_dict() for v in vacantes])


@app.route('/api/vacantes/<int:vid>', methods=['GET'])
def obtener_vacante(vid):
    return jsonify(Vacante.query.get_or_404(vid).to_dict())


@app.route('/api/vacantes', methods=['POST'])
def crear_vacante():
    data = request.get_json()
    if not data or not data.get('titulo'):
        return jsonify({'error': 'El campo titulo es requerido'}), 400
    v = Vacante(**{k: data[k] for k in ('titulo', 'tipo', 'modalidad', 'descripcion') if k in data})
    db.session.add(v)
    db.session.commit()
    return jsonify(v.to_dict()), 201


@app.route('/api/vacantes/<int:vid>', methods=['PUT'])
def actualizar_vacante(vid):
    vacante = Vacante.query.get_or_404(vid)
    data = request.get_json()
    for campo in ('titulo', 'tipo', 'modalidad', 'descripcion', 'activa'):
        if campo in data:
            setattr(vacante, campo, bool(data[campo]) if campo == 'activa' else data[campo])
    db.session.commit()
    return jsonify(vacante.to_dict())


@app.route('/api/vacantes/<int:vid>', methods=['DELETE'])
def eliminar_vacante(vid):
    vacante = Vacante.query.get_or_404(vid)
    vacante.activa = False
    db.session.commit()
    return jsonify({'mensaje': 'Vacante desactivada correctamente'})


# ── RUTAS: APLICACIONES ────────────────────────────────────────────────────────

@app.route('/api/vacantes/<int:vid>/aplicar', methods=['POST'])
def aplicar_vacante(vid):
    Vacante.query.get_or_404(vid)
    data = request.get_json()
    if not data or not data.get('nombre') or not data.get('email'):
        return jsonify({'error': 'nombre y email son requeridos'}), 400
    a = Aplicacion(vacante_id=vid, **{k: data.get(k) for k in ('nombre', 'email', 'telefono', 'mensaje')})
    db.session.add(a)
    db.session.commit()
    return jsonify({'mensaje': '¡Aplicación enviada correctamente!', 'id': a.id}), 201


@app.route('/api/aplicaciones', methods=['GET'])
def listar_aplicaciones():
    return jsonify([a.to_dict() for a in Aplicacion.query.order_by(Aplicacion.enviado_en.desc()).all()])


@app.route('/api/vacantes/<int:vid>/aplicaciones', methods=['GET'])
def aplicaciones_por_vacante(vid):
    Vacante.query.get_or_404(vid)
    return jsonify([a.to_dict() for a in Aplicacion.query.filter_by(vacante_id=vid).all()])


# ── DATOS DE EJEMPLO ───────────────────────────────────────────────────────────

def poblar_db():
    if Vacante.query.count() > 0:
        return
    ejemplos = [
        ('Vendedor/a de Mostrador',  'Tiempo completo', 'Presencial', 'Atención al cliente y manejo de inventario.'),
        ('Técnico Electricista',     'Tiempo completo', 'Presencial', 'Instalaciones eléctricas residenciales y comerciales.'),
        ('Repartidor / Mensajero',   'Tiempo completo', 'Presencial', 'Entrega de pedidos en la zona metropolitana.'),
        ('Asistente Administrativo', 'Medio tiempo',    'Presencial', 'Apoyo en facturación y cuentas por cobrar.'),
    ]
    db.session.add_all([Vacante(titulo=t, tipo=tp, modalidad=m, descripcion=d) for t, tp, m, d in ejemplos])
    db.session.commit()
    print('✅  Vacantes de ejemplo creadas.')


    app.run(debug=True, port=5000)
with app.app_context():
    db.create_all()
    poblar_db()
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        poblar_db()
    
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
