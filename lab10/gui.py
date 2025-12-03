import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from models import (
    init_db,
    get_session,
    Client,
    Driver,
    Vehicle,
    Order,
    TripDetails,
    TripLog,
)

DATE_FORMAT = "%Y-%m-%d %H:%M"  # формат дати для введення


class TransportApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Transport Company DB (Lab 10)")
        self.geometry("900x600")

        # ORM-сесія
        init_db()
        self.session = get_session()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Створюємо вкладки
        self.client_tab = ClientsTab(self.notebook, self.session)
        self.driver_tab = DriversTab(self.notebook, self.session)
        self.vehicle_tab = VehiclesTab(self.notebook, self.session)
        self.order_tab = OrdersTab(self.notebook, self.session)
        self.trip_tab = TripsTab(self.notebook, self.session)

        self.notebook.add(self.client_tab, text="Clients")
        self.notebook.add(self.driver_tab, text="Drivers")
        self.notebook.add(self.vehicle_tab, text="Vehicles")
        self.notebook.add(self.order_tab, text="Orders")
        self.notebook.add(self.trip_tab, text="Trips")

    def on_closing(self):
        self.session.close()
        self.destroy()


# --------- Базовий таб з таблицею та CRUD ---------

class BaseTab(ttk.Frame):
    def __init__(self, parent, session):
        super().__init__(parent)
        self.session = session

        self.tree = ttk.Treeview(self, show="headings")
        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.btn_add = ttk.Button(btn_frame, text="Додати", command=self.add_record)
        self.btn_edit = ttk.Button(btn_frame, text="Редагувати", command=self.edit_record)
        self.btn_delete = ttk.Button(btn_frame, text="Видалити", command=self.delete_record)
        self.btn_refresh = ttk.Button(btn_frame, text="Оновити", command=self.refresh)

        self.btn_add.pack(side=tk.LEFT, padx=5, pady=5)
        self.btn_edit.pack(side=tk.LEFT, padx=5, pady=5)
        self.btn_delete.pack(side=tk.LEFT, padx=5, pady=5)
        self.btn_refresh.pack(side=tk.LEFT, padx=5, pady=5)

    def refresh(self):
        """Перевантажити дані у таблиці (перевизначається в нащадках)."""
        pass

    def add_record(self):
        """Додати запис (перевизначається)."""
        pass

    def edit_record(self):
        """Редагувати запис (перевизначається)."""
        pass

    def delete_record(self):
        """Видалити запис (перевизначається)."""
        pass

    def get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Увага", "Виберіть запис у таблиці.")
            return None
        item = self.tree.item(sel[0])
        return item["values"][0]  # припускаємо, що перша колонка — id


# --------- Таб "Clients" ---------

class ClientsTab(BaseTab):
    def __init__(self, parent, session):
        super().__init__(parent, session)

        self.tree["columns"] = ("id", "type", "name", "contacts")
        for col, text, width in [
            ("id", "ID", 50),
            ("type", "Тип", 80),
            ("name", "Назва / ПІБ", 200),
            ("contacts", "Контакти", 250),
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=tk.W)

        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        clients = self.session.query(Client).all()
        for c in clients:
            self.tree.insert("", tk.END, values=(c.id, c.client_type, c.name, c.contacts))

    def add_record(self):
        ClientDialog(self, self.session, title="Новий клієнт")
        self.refresh()

    def edit_record(self):
        cid = self.get_selected_id()
        if cid is None:
            return
        client = self.session.query(Client).get(cid)
        if not client:
            messagebox.showerror("Помилка", "Клієнта не знайдено.")
            return
        ClientDialog(self, self.session, client=client, title="Редагувати клієнта")
        self.refresh()

    def delete_record(self):
        cid = self.get_selected_id()
        if cid is None:
            return
        if messagebox.askyesno("Підтвердження", "Видалити клієнта?"):
            client = self.session.query(Client).get(cid)
            if client:
                self.session.delete(client)
                self.session.commit()
            self.refresh()


class ClientDialog(tk.Toplevel):
    def __init__(self, parent, session, client=None, title="Клієнт"):
        super().__init__(parent)
        self.session = session
        self.client = client
        self.title(title)
        self.grab_set()

        ttk.Label(self, text="Тип (company/person):").grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="Назва / ПІБ:").grid(row=1, column=0, sticky="w")
        ttk.Label(self, text="Контакти:").grid(row=2, column=0, sticky="w")

        self.type_var = tk.StringVar(value="company")
        self.name_var = tk.StringVar()
        self.contacts_var = tk.StringVar()

        if client:
            self.type_var.set(client.client_type)
            self.name_var.set(client.name)
            self.contacts_var.set(client.contacts or "")

        ttk.Entry(self, textvariable=self.type_var).grid(row=0, column=1, pady=2, padx=5)
        ttk.Entry(self, textvariable=self.name_var).grid(row=1, column=1, pady=2, padx=5)
        ttk.Entry(self, textvariable=self.contacts_var).grid(row=2, column=1, pady=2, padx=5)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=5)

        ttk.Button(btn_frame, text="Зберегти", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Скасувати", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def save(self):
        t = self.type_var.get().strip()
        name = self.name_var.get().strip()
        contacts = self.contacts_var.get().strip()

        if not t or not name:
            messagebox.showerror("Помилка", "Тип і назва / ПІБ обов'язкові.")
            return

        if self.client is None:
            self.client = Client(client_type=t, name=name, contacts=contacts)
            self.session.add(self.client)
        else:
            self.client.client_type = t
            self.client.name = name
            self.client.contacts = contacts

        self.session.commit()
        self.destroy()


# --------- Таб "Drivers" ---------

class DriversTab(BaseTab):
    def __init__(self, parent, session):
        super().__init__(parent, session)

        self.tree["columns"] = ("id", "name", "license", "phone")
        for col, text, width in [
            ("id", "ID", 50),
            ("name", "ПІБ", 200),
            ("license", "Ліцензія", 120),
            ("phone", "Телефон", 120),
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=tk.W)

        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        drivers = self.session.query(Driver).all()
        for d in drivers:
            self.tree.insert("", tk.END, values=(d.id, d.full_name, d.license_number, d.phone))

    def add_record(self):
        DriverDialog(self, self.session, title="Новий водій")
        self.refresh()

    def edit_record(self):
        did = self.get_selected_id()
        if did is None:
            return
        driver = self.session.query(Driver).get(did)
        if not driver:
            messagebox.showerror("Помилка", "Водія не знайдено.")
            return
        DriverDialog(self, self.session, driver=driver, title="Редагувати водія")
        self.refresh()

    def delete_record(self):
        did = self.get_selected_id()
        if did is None:
            return
        if messagebox.askyesno("Підтвердження", "Видалити водія?"):
            driver = self.session.query(Driver).get(did)
            if driver:
                self.session.delete(driver)
                self.session.commit()
            self.refresh()


class DriverDialog(tk.Toplevel):
    def __init__(self, parent, session, driver=None, title="Водій"):
        super().__init__(parent)
        self.session = session
        self.driver = driver
        self.title(title)
        self.grab_set()

        ttk.Label(self, text="ПІБ:").grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="Номер ліцензії:").grid(row=1, column=0, sticky="w")
        ttk.Label(self, text="Телефон:").grid(row=2, column=0, sticky="w")

        self.name_var = tk.StringVar()
        self.lic_var = tk.StringVar()
        self.phone_var = tk.StringVar()

        if driver:
            self.name_var.set(driver.full_name)
            self.lic_var.set(driver.license_number)
            self.phone_var.set(driver.phone or "")

        ttk.Entry(self, textvariable=self.name_var).grid(row=0, column=1, pady=2, padx=5)
        ttk.Entry(self, textvariable=self.lic_var).grid(row=1, column=1, pady=2, padx=5)
        ttk.Entry(self, textvariable=self.phone_var).grid(row=2, column=1, pady=2, padx=5)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=5)
        ttk.Button(btn_frame, text="Зберегти", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Скасувати", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def save(self):
        name = self.name_var.get().strip()
        lic = self.lic_var.get().strip()
        phone = self.phone_var.get().strip()

        if not name or not lic:
            messagebox.showerror("Помилка", "ПІБ та ліцензія обов'язкові.")
            return

        if self.driver is None:
            self.driver = Driver(full_name=name, license_number=lic, phone=phone)
            self.session.add(self.driver)
        else:
            self.driver.full_name = name
            self.driver.license_number = lic
            self.driver.phone = phone

        self.session.commit()
        self.destroy()


# --------- Таб "Vehicles" ---------

class VehiclesTab(BaseTab):
    def __init__(self, parent, session):
        super().__init__(parent, session)

        self.tree["columns"] = ("id", "reg", "type", "capacity", "desc")
        for col, text, width in [
            ("id", "ID", 50),
            ("reg", "Реєстр. номер", 120),
            ("type", "Тип", 100),
            ("capacity", "Вмістимість", 100),
            ("desc", "Опис", 200),
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=tk.W)

        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        vehicles = self.session.query(Vehicle).all()
        for v in vehicles:
            self.tree.insert(
                "",
                tk.END,
                values=(v.id, v.reg_number, v.vehicle_type, v.capacity, v.description),
            )

    def add_record(self):
        VehicleDialog(self, self.session, title="Новий транспорт")
        self.refresh()

    def edit_record(self):
        vid = self.get_selected_id()
        if vid is None:
            return
        vehicle = self.session.query(Vehicle).get(vid)
        if not vehicle:
            messagebox.showerror("Помилка", "Транспорт не знайдено.")
            return
        VehicleDialog(self, self.session, vehicle=vehicle, title="Редагувати транспорт")
        self.refresh()

    def delete_record(self):
        vid = self.get_selected_id()
        if vid is None:
            return
        if messagebox.askyesno("Підтвердження", "Видалити транспорт?"):
            vehicle = self.session.query(Vehicle).get(vid)
            if vehicle:
                self.session.delete(vehicle)
                self.session.commit()
            self.refresh()


class VehicleDialog(tk.Toplevel):
    def __init__(self, parent, session, vehicle=None, title="Транспорт"):
        super().__init__(parent)
        self.session = session
        self.vehicle = vehicle
        self.title(title)
        self.grab_set()

        ttk.Label(self, text="Реєстраційний номер:").grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="Тип:").grid(row=1, column=0, sticky="w")
        ttk.Label(self, text="Вмістимість:").grid(row=2, column=0, sticky="w")
        ttk.Label(self, text="Опис:").grid(row=3, column=0, sticky="w")

        self.reg_var = tk.StringVar()
        self.type_var = tk.StringVar()
        self.cap_var = tk.StringVar()
        self.desc_var = tk.StringVar()

        if vehicle:
            self.reg_var.set(vehicle.reg_number)
            self.type_var.set(vehicle.vehicle_type or "")
            self.cap_var.set(str(vehicle.capacity) if vehicle.capacity is not None else "")
            self.desc_var.set(vehicle.description or "")

        ttk.Entry(self, textvariable=self.reg_var).grid(row=0, column=1, pady=2, padx=5)
        ttk.Entry(self, textvariable=self.type_var).grid(row=1, column=1, pady=2, padx=5)
        ttk.Entry(self, textvariable=self.cap_var).grid(row=2, column=1, pady=2, padx=5)
        ttk.Entry(self, textvariable=self.desc_var).grid(row=3, column=1, pady=2, padx=5)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=5)
        ttk.Button(btn_frame, text="Зберегти", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Скасувати", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def save(self):
        reg = self.reg_var.get().strip()
        type_ = self.type_var.get().strip()
        cap = self.cap_var.get().strip()
        desc = self.desc_var.get().strip()

        if not reg:
            messagebox.showerror("Помилка", "Реєстраційний номер обов'язковий.")
            return

        cap_val = int(cap) if cap else None

        if self.vehicle is None:
            self.vehicle = Vehicle(
                reg_number=reg,
                vehicle_type=type_,
                capacity=cap_val,
                description=desc,
            )
            self.session.add(self.vehicle)
        else:
            self.vehicle.reg_number = reg
            self.vehicle.vehicle_type = type_
            self.vehicle.capacity = cap_val
            self.vehicle.description = desc

        self.session.commit()
        self.destroy()


# --------- Таб "Orders" + TripDetails/TripLog у спрощеному вигляді ---------

class OrdersTab(BaseTab):
    def __init__(self, parent, session):
        super().__init__(parent, session)

        self.tree["columns"] = ("id", "client_id", "route", "departure", "arrival")
        for col, text, width in [
            ("id", "ID", 50),
            ("client_id", "Client ID", 80),
            ("route", "Маршрут", 200),
            ("departure", "Відправлення", 150),
            ("arrival", "Прибуття", 150),
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=tk.W)

        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        orders = self.session.query(Order).all()
        for o in orders:
            dep = o.departure_time.strftime(DATE_FORMAT) if o.departure_time else ""
            arr = o.arrival_time.strftime(DATE_FORMAT) if o.arrival_time else ""
            self.tree.insert(
                "",
                tk.END,
                values=(o.id, o.client_id, o.route, dep, arr),
            )

    def add_record(self):
        OrderDialog(self, self.session, title="Нове замовлення")
        self.refresh()

    def edit_record(self):
        oid = self.get_selected_id()
        if oid is None:
            return
        order = self.session.query(Order).get(oid)
        if not order:
            messagebox.showerror("Помилка", "Замовлення не знайдено.")
            return
        OrderDialog(self, self.session, order=order, title="Редагувати замовлення")
        self.refresh()

    def delete_record(self):
        oid = self.get_selected_id()
        if oid is None:
            return
        if messagebox.askyesno("Підтвердження", "Видалити замовлення?"):
            order = self.session.query(Order).get(oid)
            if order:
                self.session.delete(order)
                self.session.commit()
            self.refresh()


class OrderDialog(tk.Toplevel):
    def __init__(self, parent, session, order=None, title="Замовлення"):
        super().__init__(parent)
        self.session = session
        self.order = order
        self.title(title)
        self.grab_set()

        ttk.Label(self, text="Client ID:").grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="Маршрут:").grid(row=1, column=0, sticky="w")
        ttk.Label(self, text=f"Відправлення ({DATE_FORMAT}):").grid(row=2, column=0, sticky="w")
        ttk.Label(self, text=f"Прибуття ({DATE_FORMAT}):").grid(row=3, column=0, sticky="w")

        self.client_id_var = tk.StringVar()
        self.route_var = tk.StringVar()
        self.dep_var = tk.StringVar()
        self.arr_var = tk.StringVar()

        if order:
            self.client_id_var.set(str(order.client_id))
            self.route_var.set(order.route)
            if order.departure_time:
                self.dep_var.set(order.departure_time.strftime(DATE_FORMAT))
            if order.arrival_time:
                self.arr_var.set(order.arrival_time.strftime(DATE_FORMAT))

        ttk.Entry(self, textvariable=self.client_id_var).grid(row=0, column=1, pady=2, padx=5)
        ttk.Entry(self, textvariable=self.route_var).grid(row=1, column=1, pady=2, padx=5)
        ttk.Entry(self, textvariable=self.dep_var).grid(row=2, column=1, pady=2, padx=5)
        ttk.Entry(self, textvariable=self.arr_var).grid(row=3, column=1, pady=2, padx=5)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=5)
        ttk.Button(btn_frame, text="Зберегти", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Скасувати", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def parse_datetime(self, value: str):
        if not value.strip():
            return None
        try:
            return datetime.strptime(value.strip(), DATE_FORMAT)
        except ValueError:
            messagebox.showerror("Помилка", f"Невірний формат дати. Використовуйте {DATE_FORMAT}")
            return None

    def save(self):
        client_id_str = self.client_id_var.get().strip()
        route = self.route_var.get().strip()
        dep_str = self.dep_var.get().strip()
        arr_str = self.arr_var.get().strip()

        if not client_id_str or not route:
            messagebox.showerror("Помилка", "Client ID та маршрут обов'язкові.")
            return

        try:
            client_id = int(client_id_str)
        except ValueError:
            messagebox.showerror("Помилка", "Client ID має бути числом.")
            return

        dep_dt = self.parse_datetime(dep_str)
        if dep_str and dep_dt is None:
            return
        arr_dt = self.parse_datetime(arr_str)
        if arr_str and arr_dt is None:
            return

        if self.order is None:
            self.order = Order(
                client_id=client_id,
                route=route,
                departure_time=dep_dt,
                arrival_time=arr_dt,
            )
            self.session.add(self.order)
        else:
            self.order.client_id = client_id
            self.order.route = route
            self.order.departure_time = dep_dt
            self.order.arrival_time = arr_dt

        self.session.commit()
        self.destroy()


# --------- Таб "Trips" (TripDetails + TripLog у спрощеному вигляді) ---------

class TripsTab(BaseTab):
    def __init__(self, parent, session):
        super().__init__(parent, session)

        self.tree["columns"] = (
            "id",
            "order_id",
            "driver_id",
            "vehicle_id",
            "status",
            "cost",
            "log_id",
        )
        for col, text, width in [
            ("id", "ID", 40),
            ("order_id", "Order ID", 70),
            ("driver_id", "Driver ID", 70),
            ("vehicle_id", "Vehicle ID", 80),
            ("status", "Статус", 80),
            ("cost", "Вартість", 80),
            ("log_id", "TripLog ID", 80),
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=tk.W)

        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        trips = self.session.query(TripDetails).all()
        for t in trips:
            log_id = t.trip_log.id if t.trip_log else ""
            self.tree.insert(
                "",
                tk.END,
                values=(
                    t.id,
                    t.order_id,
                    t.driver_id,
                    t.vehicle_id,
                    t.status,
                    t.cost,
                    log_id,
                ),
            )

    def add_record(self):
        TripDialog(self, self.session, title="Нова поїздка")
        self.refresh()

    def edit_record(self):
        tid = self.get_selected_id()
        if tid is None:
            return
        trip = self.session.query(TripDetails).get(tid)
        if not trip:
            messagebox.showerror("Помилка", "Поїздку не знайдено.")
            return
        TripDialog(self, self.session, trip=trip, title="Редагувати поїздку")
        self.refresh()

    def delete_record(self):
        tid = self.get_selected_id()
        if tid is None:
            return
        if messagebox.askyesno("Підтвердження", "Видалити поїздку та пов'язаний лог?"):
            trip = self.session.query(TripDetails).get(tid)
            if trip:
                if trip.trip_log:
                    self.session.delete(trip.trip_log)
                self.session.delete(trip)
                self.session.commit()
            self.refresh()


class TripDialog(tk.Toplevel):
    def __init__(self, parent, session, trip=None, title="Поїздка"):
        super().__init__(parent)
        self.session = session
        self.trip = trip
        self.title(title)
        self.grab_set()

        ttk.Label(self, text="Order ID:").grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="Driver ID:").grid(row=1, column=0, sticky="w")
        ttk.Label(self, text="Vehicle ID:").grid(row=2, column=0, sticky="w")
        ttk.Label(self, text="Статус:").grid(row=3, column=0, sticky="w")
        ttk.Label(self, text="Вартість:").grid(row=4, column=0, sticky="w")
        ttk.Label(self, text=f"Факт. відпр. ({DATE_FORMAT}):").grid(row=5, column=0, sticky="w")
        ttk.Label(self, text=f"Факт. приб. ({DATE_FORMAT}):").grid(row=6, column=0, sticky="w")
        ttk.Label(self, text="Коментар:").grid(row=7, column=0, sticky="w")

        self.order_id_var = tk.StringVar()
        self.driver_id_var = tk.StringVar()
        self.vehicle_id_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.cost_var = tk.StringVar()
        self.dep_var = tk.StringVar()
        self.arr_var = tk.StringVar()
        self.comment_var = tk.StringVar()

        if trip:
            self.order_id_var.set(str(trip.order_id))
            self.driver_id_var.set(str(trip.driver_id))
            self.vehicle_id_var.set(str(trip.vehicle_id))
            self.status_var.set(trip.status or "")
            self.cost_var.set(str(trip.cost) if trip.cost is not None else "")
            if trip.trip_log:
                if trip.trip_log.actual_departure:
                    self.dep_var.set(trip.trip_log.actual_departure.strftime(DATE_FORMAT))
                if trip.trip_log.actual_arrival:
                    self.arr_var.set(trip.trip_log.actual_arrival.strftime(DATE_FORMAT))
                self.comment_var.set(trip.trip_log.comment or "")

        ttk.Entry(self, textvariable=self.order_id_var).grid(row=0, column=1, pady=2, padx=5)
        ttk.Entry(self, textvariable=self.driver_id_var).grid(row=1, column=1, pady=2, padx=5)
        ttk.Entry(self, textvariable=self.vehicle_id_var).grid(row=2, column=1, pady=2, padx=5)
        ttk.Entry(self, textvariable=self.status_var).grid(row=3, column=1, pady=2, padx=5)
        ttk.Entry(self, textvariable=self.cost_var).grid(row=4, column=1, pady=2, padx=5)
        ttk.Entry(self, textvariable=self.dep_var).grid(row=5, column=1, pady=2, padx=5)
        ttk.Entry(self, textvariable=self.arr_var).grid(row=6, column=1, pady=2, padx=5)
        ttk.Entry(self, textvariable=self.comment_var).grid(row=7, column=1, pady=2, padx=5)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=5)
        ttk.Button(btn_frame, text="Зберегти", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Скасувати", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def parse_datetime(self, value: str):
        if not value.strip():
            return None
        try:
            return datetime.strptime(value.strip(), DATE_FORMAT)
        except ValueError:
            messagebox.showerror("Помилка", f"Невірний формат дати. Використовуйте {DATE_FORMAT}")
            return None

    def save(self):
        order_id_str = self.order_id_var.get().strip()
        driver_id_str = self.driver_id_var.get().strip()
        vehicle_id_str = self.vehicle_id_var.get().strip()
        status = self.status_var.get().strip()
        cost_str = self.cost_var.get().strip()
        dep_str = self.dep_var.get().strip()
        arr_str = self.arr_var.get().strip()
        comment = self.comment_var.get().strip()

        try:
            order_id = int(order_id_str)
            driver_id = int(driver_id_str)
            vehicle_id = int(vehicle_id_str)
        except ValueError:
            messagebox.showerror("Помилка", "Order ID, Driver ID та Vehicle ID мають бути числами.")
            return

        cost = float(cost_str) if cost_str else None

        dep_dt = self.parse_datetime(dep_str)
        if dep_str and dep_dt is None:
            return
        arr_dt = self.parse_datetime(arr_str)
        if arr_str and arr_dt is None:
            return

        if self.trip is None:
            self.trip = TripDetails(
                order_id=order_id,
                driver_id=driver_id,
                vehicle_id=vehicle_id,
                status=status,
                cost=cost,
            )
            self.session.add(self.trip)
            self.session.flush()  # щоб отримати id
        else:
            self.trip.order_id = order_id
            self.trip.driver_id = driver_id
            self.trip.vehicle_id = vehicle_id
            self.trip.status = status
            self.trip.cost = cost

        if self.trip.trip_log is None and (dep_dt or arr_dt or comment):
            log = TripLog(
                trip_details=self.trip,
                actual_departure=dep_dt,
                actual_arrival=arr_dt,
                comment=comment,
            )
            self.session.add(log)
        elif self.trip.trip_log:
            self.trip.trip_log.actual_departure = dep_dt
            self.trip.trip_log.actual_arrival = arr_dt
            self.trip.trip_log.comment = comment

        self.session.commit()
        self.destroy()


if __name__ == "__main__":
    app = TransportApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
