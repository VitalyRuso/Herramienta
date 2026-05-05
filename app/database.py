from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = "sqlite:///leads.db"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)


def create_db_and_tables() -> None:
    """Crea las tablas de la base de datos si no existen."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Devuelve una sesión de base de datos."""
    with Session(engine) as session:
        yield session