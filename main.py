

import re
import math

COMMON_WORDS = {
    "password", "123456", "qwerty", "admin", "user",
    "secret", "welcome", "login", "football", "iloveyou",
    "пароль", "привіт", "student", "stud", "test"
}

def score_length(pw: str) -> int:

    n = len(pw)
    if n == 0:
        return 0
    if n < 8:
        return int(30 * n / 8)
    return min(30, 30 + int((n - 8) * 1.5))

def score_char_variety(pw: str) -> int:

    has_lower = bool(re.search(r'[a-zа-яёіїєґії]', pw, re.I))
    has_upper = bool(re.search(r'[A-ZА-ЯЁІЇЄҐ]', pw))
    has_digit = bool(re.search(r'\d', pw))
    has_symbol = bool(re.search(r'[^A-Za-zА-Яа-яЁёІЇЄҐієї0-9]', pw))
    variety = sum([has_lower, has_upper, has_digit, has_symbol])
    return int((variety / 4) * 40)

def build_personal_tokens(name: str, surname: str, date: str) -> list:

    tokens = []
    if name:
        tokens.append(name.strip())
    if surname:
        tokens.append(surname.strip())
        tokens.append(surname.replace(" ", ""))
    if date:
        d = date.strip()
        tokens.append(d)
        # цифри лише
        digits = re.sub(r'\D', '', d)
        if digits:
            tokens.append(digits)
            # різні обрізки дати (рік, день+місяць, рік+місяць)
            if len(digits) >= 4:
                tokens.append(digits[-4:])  # наприклад рік
            if len(digits) >= 6:
                tokens.append(digits[-6:])  # дмр або ін.
    # Унікалізуємо і прибираємо порожні
    return [t for t in dict.fromkeys(tokens) if t]

def contains_personal_data(pw: str, personal_tokens: list) -> list:

    found = []
    lpw = pw.lower()
    for t in personal_tokens:
        token = t.strip().lower()
        if not token:
            continue
        if token in lpw or token.replace(" ", "") in lpw:
            found.append(t)
    return found

def contains_dictionary_word(pw: str, words: set) -> list:

    found = []
    lpw = pw.lower()
    for w in words:
        if len(w) < 3:
            continue
        if w in lpw:
            found.append(w)
    return found

def estimate_strength_text(score: int) -> str:

    if score < 30:
        return "Небезпечно"
    if score < 50:
        return "Слабкий"
    if score < 70:
        return "Помірний"
    if score < 85:
        return "Хороший"
    return "Високий"

def map_to_five(final_score: int) -> int:

    if final_score < 10:
        return 0
    if final_score < 30:
        return 1
    if final_score < 50:
        return 2
    if final_score < 70:
        return 3
    if final_score < 90:
        return 4
    return 5

def security_level_from_five(five: int) -> str:
    """Короткий опис рівня безпеки від 0 до 5."""
    return {
        0: "Критично небезпечно",
        1: "Дуже слабкий",
        2: "Слабкий",
        3: "Середній",
        4: "Добрий",
        5: "Відмінний"
    }.get(five, "Н/Д")

def analyze_password(pw: str, name: str, surname: str, date: str) -> dict:
    len_sc = score_length(pw)
    var_sc = score_char_variety(pw)
    personal_tokens = build_personal_tokens(name, surname, date)
    personal_found = contains_personal_data(pw, personal_tokens)
    dict_found = contains_dictionary_word(pw, COMMON_WORDS)

    penalty = 0
    if personal_found:
        penalty += 30
    penalty += 10 * len(dict_found)

    raw_score = len_sc + var_sc  # максимум 70
    final_score = max(0, min(100, raw_score - penalty))
    rating_text = estimate_strength_text(final_score)
    five_score = map_to_five(final_score)
    sec_level = security_level_from_five(five_score)

    # Рекомендації
    recs = []
    if len(pw) < 12:
        recs.append("Збільшити довжину пароля до ≥12 символів.")
    if not re.search(r'[A-ZА-ЯЁІЇЄҐ]', pw):
        recs.append("Додати великі літери.")
    if not re.search(r'[a-zа-яёіїєґії]', pw, re.I):
        recs.append("Додати малі літери.")
    if not re.search(r'\d', pw):
        recs.append("Додати цифри.")
    if not re.search(r'[^A-Za-zА-Яа-яЁёІЇЄҐієї0-9]', pw):
        recs.append("Додати спеціальні символи (наприклад: !@#$%).")
    if personal_found:
        recs.append(f"Уникати використання персональних даних у паролі: {', '.join(personal_found)}.")
    if dict_found:
        recs.append(f"Уникати словникових слів або їх частин: {', '.join(dict_found)}.")
    if not recs:
        recs.append("Пароль виглядає добре; розгляньте менеджер паролів для унікальності пароля на різних сайтах.")

    return {
        "password_mask": '*' * len(pw),
        "length_score": len_sc,
        "variety_score": var_sc,
        "raw_score": raw_score,
        "penalty": penalty,
        "final_score": final_score,
        "rating_text": rating_text,
        "five_score": five_score,
        "security_level": sec_level,
        "personal_found": personal_found,
        "dict_found": dict_found,
        "recommendations": recs,
        "inputs": {
            "name": name,
            "surname": surname,
            "date": date
        }
    }

def pretty_print(report: dict):
    print("\n=== Результат аналізу пароля ===")
    print(f"Ім'я: {report['inputs']['name']}")
    print(f"Прізвище: {report['inputs']['surname'] or '(не введено)'}")
    print(f"Дата народження: {report['inputs']['date'] or '(не введено)'}")
    print("-------------------------------")
    print(f"Пароль: {report['password_mask']}  (пароль не виводиться повністю)")
    print(f"Оцінка довжини: {report['length_score']}/30")
    print(f"Оцінка різноманітності: {report['variety_score']}/40")
    print(f"Сирий бал (довжина+різноманітність): {report['raw_score']}/70")
    print(f"Штрафи: {report['penalty']}")
    print(f"Підсумкова оцінка: {report['final_score']}/100 -> {report['rating_text']}")
    print(f"Загальна оцінка (0-5): {report['five_score']} -> {report['security_level']}")
    if report['personal_found']:
        print("Знайдено персональні дані у паролі:", ", ".join(report['personal_found']))
    if report['dict_found']:
        print("Знайдені словникові фрагменти:", ", ".join(report['dict_found']))
    print("\nРекомендації:")
    for r in report['recommendations']:
        print(" -", r)
    print("================================\n")

def main():
    print("=== Аналіз пароля ===")
    print("Введіть лише свої (тестові) дані. Не вводьте чужі чи дуже чутливі дані у публічні системи.")
    # Ввід користувача: окремі поля
    name = input("Ім'я (обов'язково): ").strip()
    while not name:
        print("Ім'я є обов'язковим. Спробуйте ще раз.")
        name = input("Ім'я (обов'язково): ").strip()

    surname = input("Прізвище (необов'язково, натисніть Enter якщо відсутнє): ").strip()
    date = input("Дата народження (наприклад 1995-07-23 або 23.07.1995) (обов'язково): ").strip()

    pw = input("Введіть пароль для аналізу: ").strip()
    if not pw:
        print("Пароль порожній — аналіз неможливий.")
        return

    report = analyze_password(pw, name, surname, date)
    pretty_print(report)

if __name__ == "__main__":
    main()
