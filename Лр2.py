import tkinter as tk
from tkinter import ttk, scrolledtext
from tabulate import tabulate
import string
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from math import gcd

# --- 1. КОНСТАНТИ ТА ДАНІ ---
ALPHABET_UA = 'АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ'
ALPHABET_UA_LOWER = 'абвгґдеєжзиіїйклмнопрстуфхцчшщьюя'
ALPHABET_LEN = len(ALPHABET_UA)

# Еталонні частоти для української мови
UA_FREQ_EXPECTED = {
    'А': 7.6, 'Е': 6.9, 'Н': 6.6, 'І': 5.8, 'Т': 5.6, 'О': 5.3, 'Р': 4.8, 'И': 4.6,
    'В': 4.5, 'С': 4.0, 'К': 3.7, 'Л': 3.6, 'П': 3.4, 'М': 3.2, 'Д': 2.8, 'У': 2.6,
    'Я': 2.5, 'З': 2.2, 'Ч': 1.8, 'Б': 1.6, 'Й': 1.4, 'Х': 1.2, 'Ж': 1.0, 'Г': 0.9,
    'Ц': 0.8, 'Є': 0.7, 'Ї': 0.6, 'Ш': 0.6, 'Ю': 0.5, 'Щ': 0.4, 'Ф': 0.3, 'Ґ': 0.1,
    'Ь': 0.0
}
EXPECTED_FREQ_VECTOR = np.array([UA_FREQ_EXPECTED.get(ALPHABET_UA[i], 0.0) / 100 for i in range(ALPHABET_LEN)])


# --- 2. ЛОГІКА ШИФРУВАННЯ ---

def generate_caesar_key(date_str):
    total_sum = 0
    for char in date_str:
        if char.isdigit():
            total_sum += int(char)
    return total_sum % ALPHABET_LEN


def generate_vigenere_key(surname):
    key = "".join(filter(lambda x: x.isalpha(), surname)).upper()
    return key if key else "КРИПТО"


def process_text(text, shift, cipher_type='caesar', mode='encrypt', key_stream=None):
    result = ""
    stream_index = 0

    for char in text:
        current_shift = shift

        if cipher_type == 'vigenere' and key_stream and (char in ALPHABET_UA or char in ALPHABET_UA_LOWER):
            key_char = key_stream[stream_index]
            key_idx = ALPHABET_UA.find(key_char)
            current_shift = key_idx

            if mode == 'decrypt':
                current_shift = -current_shift

            stream_index = (stream_index + 1) % len(key_stream)

        if char in ALPHABET_UA:
            alphabet = ALPHABET_UA
            index = alphabet.find(char)
            new_index = (index + current_shift) % ALPHABET_LEN
            result += alphabet[new_index]
        elif char in ALPHABET_UA_LOWER:
            alphabet = ALPHABET_UA_LOWER
            index = alphabet.find(char)
            new_index = (index + current_shift) % ALPHABET_LEN
            result += alphabet[new_index]
        else:
            result += char
    return result


def vigenere_key_stream(plaintext, key):
    key_stream = ""
    key_index = 0
    key_upper = key.upper()
    for char in plaintext:
        if char in ALPHABET_UA or char in ALPHABET_UA_LOWER:
            key_stream += key_upper[key_index % len(key_upper)]
            key_index += 1
        else:
            key_stream += char
    return key_stream


def caesar_decrypt(ciphertext, shift):
    return process_text(ciphertext, -shift, cipher_type='caesar', mode='decrypt')


# --- 3. ФУНКЦІЇ КРИПТОАНАЛІЗУ ---

def get_frequency_count(text):
    text_upper = "".join(filter(lambda x: x in ALPHABET_UA, text.upper()))
    counts = {char: 0 for char in ALPHABET_UA}
    for char in text_upper:
        counts[char] += 1
    return counts, len(text_upper)


def get_frequency_perc(text):
    counts, total_letters = get_frequency_count(text)
    if total_letters == 0:
        return {char: 0 for char in ALPHABET_UA}

    frequencies = {char: (count / total_letters * 100) for char, count in counts.items()}
    return frequencies


def analyze_caesar_frequency(ciphertext):
    cipher_freq = get_frequency_perc(ciphertext)

    if not cipher_freq or max(cipher_freq.values()) == 0:
        return "Недостатньо літер для частотного аналізу.", 0

    most_common_cipher = max(cipher_freq, key=cipher_freq.get)

    idx_cipher = ALPHABET_UA.find(most_common_cipher)
    idx_expected = ALPHABET_UA.find('А')

    guessed_shift = (idx_cipher - idx_expected) % ALPHABET_LEN

    output = "--- ЧАСТОТНИЙ АНАЛІЗ (ШИФР ЦЕЗАРЯ) ---\n"
    output += f"1. Найчастіша літера в шифротексті: '{most_common_cipher}' ({cipher_freq[most_common_cipher]:.2f}%)\n"
    output += f"2. Очікувана найчастіша літера (гіпотеза): 'А'\n"
    output += f"3. Обчислений зсув: ({idx_cipher} - {idx_expected}) mod {ALPHABET_LEN} = {guessed_shift}\n"

    decrypted_text = caesar_decrypt(ciphertext, guessed_shift)
    output += "\n--- ЙМОВІРНЕ РОЗШИФРУВАННЯ (за гіпотезою 'А') ---\n"
    output += decrypted_text[:100] + "..."

    return output, guessed_shift


def calculate_ic(text):
    counts, total_letters = get_frequency_count(text)

    if total_letters < 2:
        return 0.0

    sum_ni_ni_minus_1 = sum(count * (count - 1) for count in counts.values())
    ic = sum_ni_ni_minus_1 / (total_letters * (total_letters - 1))
    return ic


def kasiski_test(ciphertext, max_key_len=10):
    text_upper = "".join(filter(lambda x: x in ALPHABET_UA, ciphertext.upper()))

    results = {}
    for length in range(3, 6):
        for i in range(len(text_upper) - length):
            sequence = text_upper[i:i + length]
            if sequence in results:
                results[sequence].append(i)
            else:
                results[sequence] = [i]

    repeated = {seq: positions for seq, positions in results.items() if len(positions) > 1}

    if not repeated:
        return "Не знайдено повторюваних послідовностей для аналізу Касіскі. Спробуйте довший текст.", []

    output = "--- МЕТОД КАСІСКІ: ПОШУК ПОВТОРЕНЬ ---\n"
    all_distances = []

    for seq, positions in repeated.items():
        distances = [positions[i] - positions[i - 1] for i in range(1, len(positions))]
        output += f"Послідовність '{seq}': Позиції: {positions}, Відстані: {distances}\n"
        all_distances.extend(distances)

    if not all_distances:
        return output + "Не знайдено відстаней для аналізу НСД.", []

    g = all_distances[0]
    for distance in all_distances[1:]:
        g = gcd(g, distance)

    output += f"\n--- ВИЗНАЧЕННЯ ДОВЖИНИ КЛЮЧА ---\n"
    output += f"Знайдені відстані: {sorted(list(set(all_distances)))}\n"
    output += f"Обчислений НСД для відстаней (ймовірна довжина ключа): {g}\n"

    possible_lengths = [i for i in range(1, max_key_len + 1) if g % i == 0]

    return output, possible_lengths


def vigenere_index_of_coincidence_test(ciphertext, max_len=10):
    text_upper = "".join(filter(lambda x: x in ALPHABET_UA, ciphertext.upper()))

    ics = {}
    IC_UA_EXPECTED = 0.057

    for length in range(1, max_len + 1):
        ic_sum = 0
        for i in range(length):
            sub_text = text_upper[i::length]
            ic_sum += calculate_ic(sub_text)

        ics[length] = ic_sum / length

    output = "--- ІНДЕКС ЗБІГУ (IC) ДЛЯ ВИЗНАЧЕННЯ ДОВЖИНИ КЛЮЧА ---\n"

    ic_data = []
    best_length = 1
    min_diff = float('inf')

    for length, ic_val in ics.items():
        ic_data.append([length, f"{ic_val:.4f}"])
        diff = abs(ic_val - IC_UA_EXPECTED)
        if diff < min_diff:
            min_diff = diff
            best_length = length

    output += tabulate(ic_data, headers=["Довжина ключа (L)", "Середній IC"], tablefmt="fancy_grid")
    output += f"\nГіпотеза: Найкраща довжина ключа (IC найближчий до {IC_UA_EXPECTED:.4f}): {best_length}"

    return output, ics


def caesar_brute_force(ciphertext, correct_shift):

    # Виконуємо повний перебір і формуємо повний список результатів
    all_results = [
        [i, f"{caesar_decrypt(ciphertext, i)[:35]}...", " <--- ПРАВИЛЬНИЙ КЛЮЧ" if i == correct_shift else ""]
        for i in range(1, ALPHABET_LEN + 1)
    ]

    # Визначаємо, які індекси потрібно відобразити (зсув - 1)
    indices_to_display = list(range(10))  # Перші 10 (зсуви 1-10)

    # Додаємо індекс правильного зсуву, якщо він не входить у перші 10
    if correct_shift > 10 and correct_shift < ALPHABET_LEN:
        indices_to_display.append(correct_shift - 1)

    # Додаємо індекс останнього зсуву, якщо він не збігається з правильним і не входить у перші 10
    if ALPHABET_LEN > 10 and ALPHABET_LEN != correct_shift:
        indices_to_display.append(ALPHABET_LEN - 1)

    # Створюємо унікальний та відсортований список індексів
    unique_indices = sorted(list(set(indices_to_display)))

    display_results = []
    last_index = -1

    # Формуємо компактний список для відображення
    for idx in unique_indices:
        if idx > last_index + 1 and last_index != -1:
            # Додаємо "..." якщо є пропуск у послідовності зсувів
            display_results.append([f"...", f"...", f"..."])

        display_results.append(all_results[idx])
        last_index = idx

    output = "--- BRUTE FORCE АТАКА (ПОВНИЙ ПЕРЕБІР) ---\n"
    output += f"ВСЬОГО СПРОБ: {ALPHABET_LEN}\n"

    output += tabulate(display_results, headers=["Зсув", "Частина розшифрованого тексту", "Статус"],
                       tablefmt="fancy_grid")
    output += "\n\nПРИМІТКА: Виконано повний перебір усіх 33 зсувів. Відображено початок, правильний та кінець для компактності."
    return output


# --- 4. РЕАЛІЗАЦІЯ ГРАФІЧНОГО ІНТЕРФЕЙСУ (TKINTER) ---

class CipherApp:
    def __init__(self, master):
        self.master = master
        master.title("Порівняльний аналіз шифрів")
        master.geometry("1000x850")

        style = ttk.Style()
        style.configure('TLabel', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10, 'bold'))
        style.configure('TNotebook.Tab', font=('Arial', 10, 'bold'))

        self.default_text = "Захист інформації – важлива дисципліна."
        self.default_date = "18.11.2004"
        self.default_surname = "Піддубний"

        self.current_ciphertext = ""
        self.current_cipher_type = "Цезар"
        self.caesar_shift = 0
        self.vigenere_key = ""
        self.original_text = ""

        self.create_widgets()



    def create_widgets(self):

        # Заголовок
        ttk.Label(self.master, text="Технічне завдання: Демонстрація Шифрів Цезаря та Віженера",
                  font=('Arial', 12, 'bold')).pack(pady=10)

        # --- Фрейм для ВХІДНИХ ДАНИХ та ВИБОРУ АЛГОРИТМУ ---
        settings_frame = ttk.LabelFrame(self.master, text="ВХІДНІ ДАНІ ТА ВИБІР АЛГОРИТМУ", padding="10")
        settings_frame.pack(padx=10, pady=5, fill="x")

        # 1. Поля для ключів
        key_frame = ttk.Frame(settings_frame)
        key_frame.pack(fill="x", pady=5)

        ttk.Label(key_frame, text="Дата (дд.мм.рррр) для Цезаря:").grid(row=0, column=0, sticky="w", padx=5)
        self.date_var = tk.StringVar(value=self.default_date)
        ttk.Entry(key_frame, textvariable=self.date_var, width=15).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(key_frame, text="Прізвище для Віженера:").grid(row=0, column=2, sticky="w", padx=20)
        self.surname_var = tk.StringVar(value=self.default_surname)
        ttk.Entry(key_frame, textvariable=self.surname_var, width=15).grid(row=0, column=3, sticky="w", padx=5)

        # 2. Вибір алгоритму
        algorithm_frame = ttk.Frame(settings_frame)
        algorithm_frame.pack(fill="x", pady=5)

        ttk.Label(algorithm_frame, text="Вибрати алгоритм:").grid(row=0, column=0, sticky="w", padx=5)
        self.cipher_choice = tk.StringVar(value="Цезар")
        ttk.Radiobutton(algorithm_frame, text="Шифр Цезаря", variable=self.cipher_choice, value="Цезар").grid(row=0,
                                                                                                              column=1,
                                                                                                              padx=10)
        ttk.Radiobutton(algorithm_frame, text="Шифр Віженера", variable=self.cipher_choice, value="Віженер").grid(row=0,
                                                                                                                  column=2,
                                                                                                                  padx=10)

        # 3. Текстове поле для вхідного тексту
        ttk.Label(settings_frame, text="Вхідний текст:").pack(anchor="w", padx=5, pady=2)
        self.text_input = scrolledtext.ScrolledText(settings_frame, height=4, width=80, font=("Arial", 10))
        self.text_input.insert(tk.END, self.default_text)
        self.text_input.pack(padx=5, pady=5, fill="x")

        # 4. Кнопки дії
        action_frame = ttk.Frame(settings_frame)
        action_frame.pack(fill="x", pady=10)

        self.encrypt_button = ttk.Button(action_frame, text="З А Ш И Ф Р У В А Т И", command=self.run_encrypt,
                                         style='TButton')
        self.encrypt_button.pack(side=tk.LEFT, expand=True, fill="x", padx=5)

        self.decrypt_button = ttk.Button(action_frame, text="Р О З Ш И Ф Р У В А Т И", command=self.run_decrypt,
                                         style='TButton', state=tk.DISABLED)
        self.decrypt_button.pack(side=tk.LEFT, expand=True, fill="x", padx=5)

        # --- Блокнот для РЕЗУЛЬТАТІВ ---
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(padx=10, pady=5, fill="both", expand=True)

        # Вкладки
        self.results_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.results_frame, text="1. Демонстрація")
        self.create_results_tab()

        self.comparison_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.comparison_frame, text="2. Порівняльний Аналіз")
        self.create_comparison_tab()

        self.crypto_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.crypto_frame, text="3. Криптоаналіз")
        self.create_crypto_tab()

        self.visualization_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.visualization_frame, text="4. Візуалізація")
        self.create_visualization_tab()

    def create_results_tab(self):
        self.results_text = scrolledtext.ScrolledText(self.results_frame, wrap=tk.WORD, width=100, height=30,
                                                      font=("Courier", 10))
        self.results_text.pack(fill="both", expand=True)
        self.results_text.insert(tk.END, "Виберіть алгоритм та натисніть 'ЗАШИФРУВАТИ'.")

    def create_comparison_tab(self):
        comparison_output = self.generate_comparison_analysis()
        self.comparison_text = scrolledtext.ScrolledText(self.comparison_frame, wrap=tk.WORD, width=100, height=30,
                                                         font=("Courier", 10))
        self.comparison_text.pack(fill="both", expand=True)
        self.comparison_text.insert(tk.END, comparison_output)

    def create_crypto_tab(self):
        self.crypto_text = scrolledtext.ScrolledText(self.crypto_frame, wrap=tk.WORD, width=100, height=30,
                                                     font=("Courier", 10))
        self.crypto_text.pack(fill="both", expand=True)
        self.crypto_text.insert(tk.END, "Результати криптоаналізу з'являться тут.")

    def create_visualization_tab(self):
        self.plot_canvas_frame = ttk.Frame(self.visualization_frame)
        self.plot_canvas_frame.pack(fill="both", expand=True)

        ttk.Label(self.visualization_frame,
                  text="Візуалізація частотного аналізу (Цезар) або Індексу Збігу (Віженер).").pack(pady=5)

        self.plot_placeholder = ttk.Label(self.plot_canvas_frame, text="Графік з'явиться після шифрування.",
                                          anchor="center")
        self.plot_placeholder.pack(fill="both", expand=True)
        self.canvas = None

    def draw_frequency_graph(self, text1, text2, label1, label2):
        freq1 = get_frequency_perc(text1)
        freq2 = get_frequency_perc(text2)

        labels = list(ALPHABET_UA)
        data1 = [freq1.get(char, 0) for char in labels]
        data2 = [freq2.get(char, 0) for char in labels]

        fig, ax = plt.subplots(figsize=(10, 5))

        x = np.arange(ALPHABET_LEN)
        width = 0.35

        ax.bar(x - width / 2, data1, width, label=label1, color='blue', alpha=0.6)
        ax.bar(x + width / 2, data2, width, label=label2, color='red', alpha=0.6)

        ax.set_ylabel('Частота (%)')
        ax.set_title('Частотний аналіз: Вихідний vs Шифр Цезаря')
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        plt.tight_layout()

        self._update_plot_canvas(fig)

    def draw_ic_graph(self, ics):

        IC_UA_EXPECTED = 0.057
        IC_RANDOM_EXPECTED = 1.0 / ALPHABET_LEN

        lengths = list(ics.keys())
        ic_values = list(ics.values())

        fig, ax = plt.subplots(figsize=(10, 5))

        ax.plot(lengths, ic_values, marker='o', linestyle='-', color='purple', label='Середній IC')
        ax.axhline(IC_UA_EXPECTED, color='green', linestyle='--', label=f'IC Укр. ({IC_UA_EXPECTED:.4f})')
        ax.axhline(IC_RANDOM_EXPECTED, color='gray', linestyle=':', label=f'IC Випадк. ({IC_RANDOM_EXPECTED:.4f})')

        ax.set_xlabel('Гіпотетична довжина ключа (L)')
        ax.set_ylabel('Індекс Збігу (IC)')
        ax.set_title('Індекс Збігу для визначення довжини ключа Віженера')
        ax.set_xticks(lengths)
        ax.legend()
        plt.tight_layout()

        self._update_plot_canvas(fig)

    def _update_plot_canvas(self, fig):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()

        self.plot_placeholder.pack_forget()
        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_crypto_tab(self, cipher_type, ciphertext):
        self.crypto_text.delete("1.0", tk.END)

        if cipher_type == "Цезар":
            # 1. Brute Force
            brute_output = caesar_brute_force(ciphertext, self.caesar_shift)
            self.crypto_text.insert(tk.END, brute_output + "\n\n")

            # 2. Частотний аналіз
            freq_output, _ = analyze_caesar_frequency(ciphertext)
            self.crypto_text.insert(tk.END, freq_output)

            # Візуалізація: Частотний графік
            self.draw_frequency_graph(self.original_text, ciphertext, "Вихідний текст", "Шифр Цезаря")

        elif cipher_type == "Віженер":
            # 1. Метод Касіскі
            kasiski_output, _ = kasiski_test(ciphertext)
            self.crypto_text.insert(tk.END, kasiski_output + "\n\n")

            # 2. Індекс Збігу
            ic_output, ics = vigenere_index_of_coincidence_test(ciphertext)
            self.crypto_text.insert(tk.END, ic_output)

            # Візуалізація: Графік Індексу Збігу
            self.draw_ic_graph(ics)

    def run_encrypt(self):
        # Зчитування та генерація ключів
        self.original_text = self.text_input.get("1.0", tk.END).strip()
        date_str = self.date_var.get().strip()
        surname = self.surname_var.get().strip()

        self.caesar_shift = generate_caesar_key(date_str)
        self.vigenere_key = generate_vigenere_key(surname)

        cipher_type = self.cipher_choice.get()
        self.current_cipher_type = cipher_type

        # Шифрування
        if cipher_type == "Цезар":
            self.current_ciphertext = process_text(self.original_text, self.caesar_shift, cipher_type='caesar',
                                                   mode='encrypt')
            key_info = f"Зсув: {self.caesar_shift}"

        elif cipher_type == "Віженер":
            self.current_ciphertext = process_text(self.original_text, 0, cipher_type='vigenere', mode='encrypt',
                                                   key_stream=vigenere_key_stream(self.original_text,
                                                                                  self.vigenere_key))
            key_info = f"Слово: '{self.vigenere_key}'"

        # Оновлення вкладок Криптоаналізу та Візуалізації
        self.update_crypto_tab(cipher_type, self.current_ciphertext)

        # Оновлення результатів демонстрації
        results_output = f"--- ДЕМОНСТРАЦІЯ ШИФРУВАННЯ ---\n"
        results_output += f"Алгоритм: {cipher_type}\n"
        results_output += f"Використаний ключ: {key_info}\n"
        results_output += f"Вхідний текст: {self.original_text[:60]}...\n"
        results_output += "\n--- ЗАШИФРОВАНИЙ ТЕКСТ ---\n"
        results_output += self.current_ciphertext

        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, results_output)

        self.decrypt_button.config(state=tk.NORMAL)

    def run_decrypt(self):
        if not self.current_ciphertext:
            self.results_text.insert(tk.END, "\n\nПомилка: Немає зашифрованих даних для розшифрування.")
            return

        cipher_type = self.current_cipher_type

        # Розшифрування
        if cipher_type == "Цезар":
            decrypted_text = caesar_decrypt(self.current_ciphertext, self.caesar_shift)
            key_info = f"Зсув: {self.caesar_shift}"
        elif cipher_type == "Віженер":
            decrypted_text = process_text(self.current_ciphertext, 0, cipher_type='vigenere', mode='decrypt',
                                          key_stream=vigenere_key_stream(self.current_ciphertext, self.vigenere_key))
            key_info = f"Слово: '{self.vigenere_key}'"
        else:
            decrypted_text = "Помилка розшифрування."
            key_info = ""

        # Оновлення результатів
        results_output = "\n\n--- Р О З Ш И Ф Р У В А Н Н Я ---\n"
        results_output += f"Алгоритм: {cipher_type}\n"
        results_output += f"Використаний ключ: {key_info}\n"
        results_output += f"Результат:\n{decrypted_text}\n"
        results_output += f"(Збіг з оригіналом: {decrypted_text == self.original_text})"

        self.results_text.insert(tk.END, results_output)
        self.results_text.see(tk.END)

    def generate_comparison_analysis(self):
        comparison_data = [
            ["Ключ", "Зсув (число)", "Ключове слово"],
            ["Тип заміни", "Моноалфавітний", "Поліалфавітний"],
            ["Метод зламу", "Brute Force, Частотний аналіз", "Метод Касіскі, Індекс Збігу"],
            ["Криптостійкість", "Дуже низька", "Середня (якщо ключ короткий)"]
        ]

        comparison_output = "--- ПОРІВНЯЛЬНИЙ АНАЛІЗ: ЦЕЗАРЬ VS ВІЖЕНЕР ---\n"
        comparison_output += tabulate(comparison_data, headers=["Характеристика", "Цезарь", "Віженер"],
                                      tablefmt="fancy_grid")

        comparison_output += "\n\n--- ВИСНОВКИ ПРО СТІЙКІСТЬ ---\n"
        comparison_output += "Шифр Цезаря:Криптоаналіз зводиться до перебору 33 варіантів (Brute Force) або до порівняння частот літер."
        comparison_output += "Шифр Віженера: Вимагає складніших атак: Метод Касіскі для знаходження довжини ключа та Індексу Збігу для підтвердження."

        return comparison_output


# --- ЗАПУСК ПРОГРАМИ ---
if __name__ == "__main__":
    try:
        tabulate
        plt
        np.array
    except (NameError, AttributeError):
        print("Помилка: Необхідні бібліотеки 'tabulate', 'matplotlib' та 'numpy' не встановлені.")
        print("Будь ласка, встановіть їх командою: pip install tabulate matplotlib numpy")
    else:
        root = tk.Tk()
        app = CipherApp(root)
        root.mainloop()