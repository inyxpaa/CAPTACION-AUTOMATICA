from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text,
    DateTime, Boolean, ForeignKey, Enum as SAEnum, Date
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from loguru import logger

from app.core.config import config

engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=config.IS_DEV,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Contacto(Base):
    __tablename__ = "contactos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    empresa = Column(String(200), nullable=False)
    email = Column(String(200), nullable=True)
    telefono = Column(String(50), nullable=True)
    web = Column(String(300), nullable=True)
    localidad = Column(String(100), nullable=True)
    provincia = Column(String(100), default="Navarra")
    descripcion = Column(Text, nullable=True)

    modulo = Column(
        SAEnum("constructores", "alianzas", name="modulo_enum"),
        nullable=False
    )
    tipo_empresa = Column(String(100), nullable=True)
    fuente = Column(String(200), nullable=True)

    estado = Column(
        SAEnum("nuevo", "email_enviado", "respondido", "descartado", name="estado_enum"),
        default="nuevo"
    )

    fecha_captura = Column(DateTime, default=datetime.utcnow)
    notas = Column(Text, nullable=True)

    emails_enviados = relationship("EmailLog", back_populates="contacto", cascade="all, delete")

    def __repr__(self):
        return f"<Contacto {self.empresa} - {self.email}>"


class Particular(Base):
    __tablename__ = "particulares"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=True)
    telefono = Column(String(50), nullable=True)
    localidad = Column(String(100), nullable=True)
    descripcion_vivienda = Column(Text, nullable=True)
    precio_aproximado = Column(String(50), nullable=True)
    fuente = Column(String(200), nullable=True)
    url_anuncio = Column(String(500), nullable=True)

    estado = Column(
        SAEnum(
            "nuevo", "llamado", "interesado", "exclusividad",
            "vencido", "descartado",
            name="particular_estado_enum"
        ),
        default="nuevo"
    )

    fecha_exclusividad_inicio = Column(Date, nullable=True)
    fecha_exclusividad_fin = Column(Date, nullable=True)
    meses_exclusividad = Column(Integer, default=3)

    fecha_captura = Column(DateTime, default=datetime.utcnow)
    fecha_ultimo_contacto = Column(DateTime, nullable=True)
    notas = Column(Text, nullable=True)

    llamadas = relationship("LlamadaLog", back_populates="particular", cascade="all, delete")

    def __repr__(self):
        return f"<Particular {self.nombre} - {self.localidad}>"

    @property
    def dias_exclusividad_restantes(self):
        if not self.fecha_exclusividad_fin:
            return None
        delta = self.fecha_exclusividad_fin - datetime.utcnow().date()
        return delta.days


class LlamadaLog(Base):
    __tablename__ = "llamadas_log"

    id = Column(Integer, primary_key=True, index=True)
    particular_id = Column(Integer, ForeignKey("particulares.id", ondelete="CASCADE"))
    fecha = Column(DateTime, default=datetime.utcnow)
    duracion_min = Column(Integer, nullable=True)
    resultado = Column(
        SAEnum("no_responde", "rechazado", "interesado", "cita_fijada", "acuerdo", name="llamada_resultado_enum"),
        nullable=False
    )
    notas = Column(Text, nullable=True)

    particular = relationship("Particular", back_populates="llamadas")

    def __repr__(self):
        return f"<Llamada particular={self.particular_id} resultado={self.resultado}>"


class Campana(Base):
    __tablename__ = "campanas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    modulo = Column(String(50), nullable=False)
    fecha_inicio = Column(DateTime, default=datetime.utcnow)
    fecha_fin = Column(DateTime, nullable=True)
    total_enviados = Column(Integer, default=0)
    total_abiertos = Column(Integer, default=0)
    total_respondidos = Column(Integer, default=0)
    activa = Column(Boolean, default=True)
    descripcion = Column(Text, nullable=True)

    emails = relationship("EmailLog", back_populates="campana", cascade="all, delete")

    @property
    def tasa_apertura(self) -> float:
        if self.total_enviados == 0:
            return 0.0
        return round((self.total_abiertos / self.total_enviados) * 100, 1)

    def __repr__(self):
        return f"<Campana '{self.nombre}' - {self.total_enviados} enviados>"


class EmailLog(Base):
    __tablename__ = "email_log"

    id = Column(Integer, primary_key=True, index=True)
    contacto_id = Column(Integer, ForeignKey("contactos.id", ondelete="CASCADE"))
    campana_id = Column(Integer, ForeignKey("campanas.id", ondelete="CASCADE"), nullable=True)

    asunto = Column(String(300), nullable=False)
    cuerpo_html = Column(Text, nullable=False)
    cuerpo_texto = Column(Text, nullable=True)

    estado = Column(
        SAEnum("pendiente", "enviado", "error", "abierto", name="email_estado_enum"),
        default="pendiente"
    )
    resend_id = Column(String(100), nullable=True)
    error_msg = Column(Text, nullable=True)

    fecha_envio = Column(DateTime, default=datetime.utcnow)
    fecha_apertura = Column(DateTime, nullable=True)

    contacto = relationship("Contacto", back_populates="emails_enviados")
    campana = relationship("Campana", back_populates="emails")

    def __repr__(self):
        return f"<EmailLog contacto={self.contacto_id} estado={self.estado}>"


class ConfiguracionSistema(Base):
    __tablename__ = "configuracion"

    id = Column(Integer, primary_key=True)
    clave = Column(String(100), unique=True, nullable=False)
    valor = Column(Text, nullable=True)
    descripcion = Column(String(300), nullable=True)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info("Base de datos inicializada")


def get_db() -> Session:
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


@contextmanager
def db_session():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error en sesion de BD: {e}")
        raise
    finally:
        db.close()
