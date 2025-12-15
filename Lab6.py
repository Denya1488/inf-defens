import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sqlite3
import os

DB_NAME = 'students_db.db'

# Визначення типових ін'єкцій
INJECTIONS = {
    "Коректний Пошук (Іванов)": "Іванов",
    "1. Обхід Умови (' OR 1=1 --)": "' OR 1=1 --",
    "2. Обхід (IS NOT NULL)": "' OR last_name IS NOT NULL --",
    "Неіснуючий Користувач": "Дементієва"
}


# Логіка Бази Даних
def init_students_db():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Створення таблиці students
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS students
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY,
                       last_name
                       TEXT
                       NOT
                       NULL,
                       first_name
                       TEXT
                       NOT
                       NULL,
                       student_id
                       TEXT
                       UNIQUE
                       NOT
                       NULL,
                       grade_secret
                       TEXT
                   )
                   ''')

    # Тестові дані з конфіденційною інформацією
    students_data = [
        ('Іванов', 'Денис', 'STU1001', 'Оцінка з Математики: 95/100'),
        ('Петренко', 'Олена', 'STU1002', 'Середній бал: 4.9'),
        ('Коваль', 'Андрій', 'STU1003', 'Таємний код доступу: KVA-777'),
        ('Сидоренко', 'Наталія', 'STU1004', 'Оцінка з Історії: 70/100'),
        ('Громов', 'Віктор', 'STU1005', 'Закритий коментар: Високий потенціал')
    ]

    for last_name, first_name, student_id, grade_secret in students_data:
        try:
            cursor.execute(
                "INSERT INTO students (last_name, first_name, student_id, grade_secret) VALUES (?, ?, ?, ?)",
                (last_name, first_name, student_id, grade_secret)
            )
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()


# Вразливий Пошук
def vulnerable_search(search_term):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        # УРАЗЛИВИЙ ЗАПИТ: Пряме підставлення (string formatting)
        sql_query = f"SELECT last_name, first_name, student_id, grade_secret FROM students WHERE last_name = '{search_term}'"

        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()

        return sql_query, results

    except sqlite3.Error as e:
        return f"[SQL ERROR] {e}", []
    finally:
        if conn:
            conn.close()


# Захищений Пошук
def protected_search(search_term):
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        # ЗАХИЩЕНИЙ ЗАПИТ: Параметризований запит
        sql_query_template = "SELECT last_name, first_name, student_id, grade_secret FROM students WHERE last_name = ?"

        cursor = conn.cursor()
        cursor.execute(sql_query_template, (search_term,))
        results = cursor.fetchall()

        # Форматуємо SQL для відображення
        display_query = f"SELECT ... WHERE last_name = '{search_term}' (ПАРАМЕТРИЗОВАНО)"
        return display_query, results

    except sqlite3.Error as e:
        return f"[SQL ERROR] {e}", []
    finally:
        if conn:
            conn.close()


# Графічний Інтерфейс
class SQLInjectionDemoApp:
    def __init__(self, master):
        self.master = master
        master.title("SQL-Ін'єкції та Захист")
        master.geometry("850x650")  # Зменшена висота, оскільки немає лог-файлу

        # Налаштування стилів
        style = ttk.Style()
        style.configure("TLabel", font=('Arial', 10))
        style.configure("TButton", font=('Arial', 10, 'bold'))
        style.configure("TEntry", font=('Arial', 10))

        # Фрейм для вводу
        input_frame = ttk.Frame(master, padding="10 10 10 10")
        input_frame.pack(fill='x')

        # --- Combobox для вибору ін'єкції ---
        ttk.Label(input_frame, text="1. Оберіть типовий ввід:").grid(row=0, column=0, sticky='w', padx=5, pady=5)

        self.injection_choice = ttk.Combobox(input_frame, values=list(INJECTIONS.keys()), width=48, state="readonly")
        self.injection_choice.grid(row=0, column=1, sticky='we', padx=5, pady=5)
        self.injection_choice.current(0)
        self.injection_choice.bind("<<ComboboxSelected>>", self.update_entry_from_combobox)

        # --- Поле для вільного вводу ---
        ttk.Label(input_frame, text="2. Або введіть свій рядок:").grid(row=1, column=0, sticky='w', padx=5, pady=5)

        self.search_entry = ttk.Entry(input_frame, width=50)
        self.search_entry.grid(row=1, column=1, sticky='we', padx=5, pady=5)
        self.search_entry.insert(0, INJECTIONS[list(INJECTIONS.keys())[0]])

        # Кнопки
        ttk.Button(input_frame, text="Вразливий Пошук",
                   command=lambda: self.run_search(self.search_entry.get(), 'vulnerable')).grid(row=2, column=0, padx=5,
                                                                                                pady=10, sticky='we')
        ttk.Button(input_frame, text="Захищений Пошук",
                   command=lambda: self.run_search(self.search_entry.get(), 'protected')).grid(row=2, column=1, padx=5,
                                                                                               pady=10, sticky='we')

        # Фрейм для результатів
        results_frame = ttk.Frame(master, padding="10 10 10 10")
        results_frame.pack(fill='both', expand=True)

        # Поле для відображення SQL-запиту
        ttk.Label(results_frame, text="Виконаний SQL-запит:").pack(fill='x')
        self.sql_display = scrolledtext.ScrolledText(results_frame, height=3, wrap=tk.WORD, font=('Courier New', 10),
                                                     state='disabled', bg='#f0f0f0')
        self.sql_display.pack(fill='x', padx=5, pady=5)

        ttk.Label(results_frame, text="Результати БД:").pack(fill='x', pady=(10, 0))

        # Treeview для відображення результатів таблицею
        self.tree = ttk.Treeview(results_frame, columns=("lastname", "firstname", "studentid", "secret"),
                                 show='headings')
        self.tree.heading("lastname", text="Прізвище")
        self.tree.heading("firstname", text="Ім'я")
        self.tree.heading("studentid", text="ID Студента")
        self.tree.heading("secret", text="Конфіденційна Інфо")

        # Налаштування ширини стовпців
        self.tree.column("lastname", width=100)
        self.tree.column("firstname", width=100)
        self.tree.column("studentid", width=100)
        self.tree.column("secret", width=300)

        self.tree.pack(fill='both', expand=True, padx=5, pady=5)

    def update_entry_from_combobox(self, event):

        selected_key = self.injection_choice.get()
        selected_value = INJECTIONS.get(selected_key, "")

        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, selected_value)

    def display_sql(self, sql_text):

        self.sql_display.config(state='normal')
        self.sql_display.delete(1.0, tk.END)
        self.sql_display.insert(tk.END, sql_text)
        self.sql_display.config(state='disabled')

    def display_results(self, results):

        # Очищення старих результатів
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not results:
            self.tree.insert('', tk.END, values=("(Нічого не знайдено)", "", "", ""))
            return

        # Вставка нових результатів
        for row in results:
            self.tree.insert('', tk.END, values=row)

    def run_search(self, search_term, version):

        if version == 'vulnerable':
            sql_query, results = vulnerable_search(search_term)

            # Логіка для повідомлення про успішну ін'єкцію
            is_injected = len(results) > 1 and search_term.strip() not in [r[0] for r in results]

            if is_injected:
                messagebox.showerror("!!! АТАКА !!!", f"УСПІШНА ІН'ЄКЦІЯ! Витік {len(results)} записів.")
            else:
                messagebox.showwarning("Вразливий Пошук", "Виконується ВРАЗЛИВИЙ запит.")
        else:
            sql_query, results = protected_search(search_term)

            # Логіка для повідомлення про блокування атаки
            is_blocked = not results and ("'" in search_term or "=" in search_term)

            if is_blocked:
                messagebox.showinfo("БЛОКУВАННЯ", f"Спроба ін'єкції успішно заблокована.")
            else:
                messagebox.showinfo("Захищений Пошук", "Виконується ЗАХИЩЕНИЙ запит.")

        self.display_sql(sql_query)
        self.display_results(results)


if __name__ == '__main__':
    print("Ініціалізація бази даних...")
    try:
        init_students_db()
        print(f"База даних '{DB_NAME}' готова.")
    except Exception as e:
        print(f"Помилка ініціалізації: {e}")
        exit()

    root = tk.Tk()
    app = SQLInjectionDemoApp(root)
    root.mainloop()