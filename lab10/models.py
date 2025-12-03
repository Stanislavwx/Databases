from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Float,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# ---------- Підключення до БД ----------

# SQLite-файл у поточній папці
engine = create_engine("sqlite:///transport.db", echo=False)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ---------- Моделі ----------

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_type = Column(String(20), nullable=False)  # "company" або "person"
    name = Column(String(100), nullable=False)
    contacts = Column(String(200))

    orders = relationship("Order", back_populates="client")

    def __repr__(self):
        return f"<Client(id={self.id}, type={self.client_type}, name={self.name})>"


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(100), nullable=False)
    license_number = Column(String(50), nullable=False)
    phone = Column(String(50))

    trip_details = relationship("TripDetails", back_populates="driver")

    def __repr__(self):
        return f"<Driver(id={self.id}, name={self.full_name})>"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reg_number = Column(String(50), nullable=False, unique=True)
    vehicle_type = Column(String(50))
    capacity = Column(Integer)
    description = Column(String(200))

    trip_details = relationship("TripDetails", back_populates="vehicle")

    def __repr__(self):
        return f"<Vehicle(id={self.id}, reg={self.reg_number})>"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    route = Column(String(200), nullable=False)
    departure_time = Column(DateTime)
    arrival_time = Column(DateTime)

    client = relationship("Client", back_populates="orders")
    trip_details = relationship("TripDetails", back_populates="order", uselist=False)

    def __repr__(self):
        return f"<Order(id={self.id}, client_id={self.client_id}, route={self.route})>"


class TripDetails(Base):
    __tablename__ = "trip_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    status = Column(String(50))  # наприклад: planned, in_progress, done
    cost = Column(Float)

    order = relationship("Order", back_populates="trip_details")
    driver = relationship("Driver", back_populates="trip_details")
    vehicle = relationship("Vehicle", back_populates="trip_details")
    trip_log = relationship("TripLog", back_populates="trip_details", uselist=False)

    def __repr__(self):
        return f"<TripDetails(id={self.id}, order_id={self.order_id})>"


class TripLog(Base):
    __tablename__ = "trip_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trip_details_id = Column(Integer, ForeignKey("trip_details.id"), nullable=False)
    actual_departure = Column(DateTime)
    actual_arrival = Column(DateTime)
    comment = Column(String(300))

    trip_details = relationship("TripDetails", back_populates="trip_log")

    def __repr__(self):
        return f"<TripLog(id={self.id}, trip_details_id={self.trip_details_id})>"


def init_db():
    """Створити всі таблиці в БД."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Отримати нову сесію ORM."""
    return SessionLocal()


if __name__ == "__main__":
    # Для разового створення таблиць можна запустити цей файл напряму
    init_db()
    print("Таблиці створено.")
