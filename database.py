from sqlalchemy import create_engine, Column, Integer, String, Date, Enum, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import enum
import datetime

Base = declarative_base()

class TipoMovimentacao(enum.Enum):
    entrada = 'entrada'
    saida = 'saida'

class Produto(Base):
    __tablename__ = 'produtos'

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    quantidade = Column(Integer, default=0)
    estoque_minimo = Column(Integer, default=0)

class Movimentacao(Base):
    __tablename__ = 'movimentacoes'

    id = Column(Integer, primary_key=True)
    produto_id = Column(Integer, nullable=False)
    tipo = Column(Enum(TipoMovimentacao), nullable=False)
    quantidade = Column(Integer, nullable=False)
    data = Column(Date, default=datetime.date.today)

class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    senha = Column(String, nullable=False)  # Em produção, usar hash
    is_admin = Column(Boolean, default=False)

engine = create_engine('sqlite:///estoque.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# Cria um admin padrão se não existir
if not session.query(Usuario).filter_by(username="admin").first():
    admin = Usuario(nome="Administrador", username="admin", senha="admin", is_admin=True)
    session.add(admin)
    session.commit()
