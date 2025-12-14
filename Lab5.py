import tkinter as tk
from tkinter import messagebox
from hashlib import sha256
from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import re


# Генерація ключа
def generate_key(email, birthdate):
    email = (email or "").strip()
    birth = (birthdate or "").strip()

    local = email.split("@")[0] if "@" in email else email

    # Регулярний вираз для пошуку слів (латиниця та кирилиця)
    segments = re.findall(r"[A-Za-zА-Яа-яІіЇїЄєҐґ]+", local)
    segments = [s for s in segments if len(s) > 1]

    if segments:
        personal = "".join(s.capitalize() for s in segments)
        key_display = personal + birth
        data = key_display
    else:
        key_display = email + birth
        data = key_display

    key_bytes = sha256(data.encode("utf-8")).digest()
    return key_bytes, key_display


# Шифрування
def encrypt_message(message, key):
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(message.encode("utf-8"), AES.block_size))
    iv = b64encode(cipher.iv).decode("utf-8")
    ct = b64encode(ct_bytes).decode("utf-8")
    return f"{iv}:{ct}"


# Розшифрування
def decrypt_message(enc_message, key):
    try:
        iv_str, ct_str = enc_message.split(":")
        iv = b64decode(iv_str)
        ct = b64decode(ct_str)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        pt = unpad(cipher.decrypt(ct), AES.block_size)
        return pt.decode("utf-8")
    except Exception as e:
        return f"Помилка розшифрування: {e}"


# GUI
class EmailEncryptorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Шифратор")
        # Змінюємо розмір для нового макету
        self.root.geometry("650x550")

        # --- КОНТЕЙНЕР ДЛЯ ВВОДУ ДАНИХ (ВЕРХНЯ ЧАСТИНА) ---
        input_container = tk.LabelFrame(root, text="  Дані для генерації ключа ", padx=10, pady=10)
        input_container.pack(pady=10, fill="x", padx=15)

        # 1. Email
        frame_email = tk.Frame(input_container)
        frame_email.pack(pady=5, fill="x")
        tk.Label(frame_email, text="Email:").pack(side="left", anchor="w", padx=(0, 48))
        self.entry_email = tk.Entry(frame_email, width=45)
        self.entry_email.pack(side="left", fill="x", expand=True)

        # 2. Дата народження
        frame_birth = tk.Frame(input_container)
        frame_birth.pack(pady=5, fill="x")
        tk.Label(frame_birth, text="Дата (ДДММРРРР):").pack(side="left", anchor="w")
        self.entry_birth = tk.Entry(frame_birth, width=15)
        self.entry_birth.pack(side="left", padx=5)

        # 3. Ключ (індикація)
        frame_key_display = tk.Frame(input_container)
        frame_key_display.pack(pady=5, fill="x")
        self.label_key = tk.Label(frame_key_display, text="Ключ:", fg="blue", justify=tk.LEFT, anchor="w")
        self.label_key.pack(fill="x")

        # --- КНОПКИ КЕРУВАННЯ ---
        frame_controls = tk.Frame(root, padx=15, pady=5)
        frame_controls.pack(fill="x")

        # Група кнопок 1: Генерація та Тест
        frame_key_buttons = tk.Frame(frame_controls)
        frame_key_buttons.pack(side="left", padx=(0, 10))
        tk.Button(frame_key_buttons, text="1. Генерувати ключ", command=self.generate_key_gui, width=18).pack(
            side="left", padx=5)
        tk.Button(frame_key_buttons, text="Тестовий приклад", command=self.test_example, width=18).pack(side="left",
                                                                                                        padx=5)

        # Група кнопок 2: Шифрування/Розшифрування
        frame_crypto_buttons = tk.Frame(frame_controls)
        frame_crypto_buttons.pack(side="right")
        tk.Button(frame_crypto_buttons, text="Шифрувати", command=self.encrypt_gui, bg='green', fg='white',
                  width=12).pack(side="left", padx=5)
        tk.Button(frame_crypto_buttons, text="Розшифрувати", command=self.decrypt_gui, bg='red', fg='white',
                  width=12).pack(side="left", padx=5)

        # --- ВВІД ПОВІДОМЛЕННЯ ---
        frame_message_input = tk.LabelFrame(root, text="Введіть повідомлення / Ciphertext ", padx=10, pady=5)
        frame_message_input.pack(pady=5, fill="x", padx=15)

        self.entry_message = tk.Entry(frame_message_input)
        self.entry_message.pack(fill="x", expand=True, padx=0, pady=5)

        # --- РЕЗУЛЬТАТ (НИЖНЯ ЧАСТИНА) ---
        frame_result = tk.LabelFrame(root, text="Результат операції ", padx=10, pady=5)
        frame_result.pack(pady=5, fill="both", expand=True, padx=15)

        self.text_result = tk.Text(frame_result, height=10, wrap="word", padx=5, pady=5)
        self.text_result.pack(fill="both", expand=True)

        self.key = None
        self.key_display = ""
        self.enc_message = None

    #  Логіка кнопок (залишається без змін)
    def generate_key_gui(self):
        email = self.entry_email.get().strip()
        birth = self.entry_birth.get().strip()

        if not email or not birth:
            messagebox.showerror("Помилка", "Введіть Email та дату народження")
            return

        self.key, self.key_display = generate_key(email, birth)
        self.label_key.config(text=f"Ключ: {self.key_display}")
        messagebox.showinfo("Успіх", "Симетричний ключ згенеровано!")

    def encrypt_gui(self):
        if not self.key:
            messagebox.showerror("Помилка", "Спочатку згенеруйте ключ")
            return

        message = self.entry_message.get().strip()
        if not message:
            messagebox.showerror("Помилка", "Введіть повідомлення")
            return

        self.enc_message = encrypt_message(message, self.key)
        self.text_result.delete("1.0", tk.END)
        self.text_result.insert(tk.END, self.enc_message)
        self.entry_message.delete(0, tk.END)
        self.entry_message.insert(0, self.enc_message)

    def decrypt_gui(self):
        if not self.key:
            messagebox.showerror("Помилка", "Спочатку згенеруйте ключ")
            return

        input_message = self.entry_message.get().strip()
        message_to_decrypt = input_message if input_message else self.enc_message

        if not message_to_decrypt:
            messagebox.showerror("Помилка", "Введіть або зашифруйте повідомлення")
            return

        dec_message = decrypt_message(message_to_decrypt, self.key)
        self.text_result.delete("1.0", tk.END)
        self.text_result.insert(tk.END, dec_message)

        if not dec_message.startswith("Помилка"):
            self.entry_message.delete(0, tk.END)
            self.entry_message.insert(0, dec_message)
            self.enc_message = None

    def test_example(self):
        email = "taras.koval@gmail.com"
        birth = "01012001"
        message = "Зустрінемось о 12:00 на Хрещатику"

        self.entry_email.delete(0, tk.END)
        self.entry_email.insert(0, email)

        self.entry_birth.delete(0, tk.END)
        self.entry_birth.insert(0, birth)

        self.entry_message.delete(0, tk.END)
        self.entry_message.insert(0, message)

        self.key, self.key_display = generate_key(email, birth)
        self.label_key.config(text=f"Ключ: {self.key_display}")

        self.enc_message = encrypt_message(message, self.key)

        self.text_result.delete("1.0", tk.END)
        self.text_result.insert(tk.END, f"--- ТЕСТОВИЙ ПРИКЛАД ---\n")
        self.text_result.insert(tk.END, f"Ключова фраза: {self.key_display}\n")
        self.text_result.insert(tk.END, f"Вихідне повідомлення: {message}\n\n")
        self.text_result.insert(tk.END, f"Зашифроване повідомлення:\n{self.enc_message}\n\n")

        dec_message = decrypt_message(self.enc_message, self.key)
        self.text_result.insert(tk.END, f"Розшифроване повідомлення:\n{dec_message}")

        self.entry_message.delete(0, tk.END)
        self.entry_message.insert(0, self.enc_message)


# Запуск
if __name__ == "__main__":
    root = tk.Tk()
    app = EmailEncryptorApp(root)
    root.mainloop()