import os
import platform
import subprocess
from PIL import Image


# === ДОПОМІЖНІ ФУНКЦІЇ ===

def text_to_bits(text):
    """Конвертація тексту у двійковий формат"""
    return ''.join(format(ord(c), '08b') for c in text)


def bits_to_text(bits):
    """Зворотна конвертація"""
    chars = [bits[i:i + 8] for i in range(0, len(bits), 8)]
    result = []
    for b in chars:
        if len(b) == 8:
            char_code = int(b, 2)
            # Перевірка на валідність символу
            if 0 < char_code < 1114112:  # Діапазон Unicode
                try:
                    result.append(chr(char_code))
                except ValueError:
                    pass
    return ''.join(result)


# === ОСНОВНА ЛОГІКА ===

def hide_message(input_path, output_path, message):
    """Приховує повідомлення у PNG-зображенні"""
    print("\n" + "=" * 70)
    print("  ПРОЦЕС ПРИХОВУВАННЯ")
    print("=" * 70)

    # Крок 1: Завантаження зображення
    print("\n[1/5] Завантаження зображення...")
    img = Image.open(input_path)
    img = img.convert('RGB')
    pixels = img.load()
    width, height = img.size
    print(f"      Розмір: {width}x{height} пікселів")
    print(f"      Максимальна ємність: {(width * height * 3) // 8} символів")

    # Крок 2: Конвертація у біти
    print("\n[2/5] Конвертація у біти...")
    start_marker = "11111110111111101111111011111110"  # Унікальний маркер початку (32 біта)
    end_marker = "10101010101010101010101010101010"  # Унікальний маркер кінця (32 біта)
    message_bits = start_marker + text_to_bits(message) + end_marker

    print(f"      Довжина повідомлення: {len(message)} символів")
    print(f"      У бітах (з маркерами): {len(message_bits)} біт")
    print(f"      Перші 32 біти: {message_bits[:32]}...")

    # Перевірка ємності
    max_bits = width * height * 3
    if len(message_bits) > max_bits:
        raise ValueError(f"Повідомлення занадто довге! Макс: {max_bits // 8} символів")

    # Крок 3: Вбудовування
    print("\n[3/5] Вбудовування бітів у пікселі...")
    data_index = 0
    modified_pixels = 0

    for y in range(height):
        for x in range(width):
            if data_index >= len(message_bits):
                break

            r, g, b = pixels[x, y]
            original = (r, g, b)

            # Замінюємо молодші біти
            if data_index < len(message_bits):
                r = (r & ~1) | int(message_bits[data_index])
                data_index += 1
            if data_index < len(message_bits):
                g = (g & ~1) | int(message_bits[data_index])
                data_index += 1
            if data_index < len(message_bits):
                b = (b & ~1) | int(message_bits[data_index])
                data_index += 1

            pixels[x, y] = (r, g, b)

            if (r, g, b) != original:
                modified_pixels += 1

        if data_index >= len(message_bits):
            break

    print(f"      Модифіковано пікселів: {modified_pixels}")
    print(f"      Відсоток зміни: {(modified_pixels / (width * height) * 100):.2f}%")

    # Крок 4: Збереження
    print("\n[4/5] Збереження стегозображення...")
    img.save(output_path, "PNG")
    print(f"      Файл збережено: {output_path}")

    # Закриваємо зображення перед аналізом
    img.close()

    # Крок 5: Аналіз розмірів
    print("\n[5/5] Аналіз результатів:")
    orig_size = os.path.getsize(input_path)
    stego_size = os.path.getsize(output_path)
    print(f"      Оригінал: {orig_size:,} байт")
    print(f"      Стего: {stego_size:,} байт")
    print(f"      Різниця: {abs(stego_size - orig_size):,} байт")

    # Відкриття файлу
    try:
        if platform.system() == "Windows":
            os.startfile(output_path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", output_path], check=False)
        else:
            subprocess.run(["xdg-open", output_path], check=False)
        print("\n[+] Стегозображення відкрито у переглядачі")
    except Exception:
        print("\n[!] Не вдалося автоматично відкрити файл")

    print("\n" + "=" * 70)
    print("  ПРИХОВУВАННЯ ЗАВЕРШЕНО")
    print("=" * 70)


def extract_message(image_path):
    """Витягує повідомлення з PNG-зображення"""
    print("\n" + "=" * 70)
    print("  ПРОЦЕС ВИТЯГУВАННЯ")
    print("=" * 70)

    print("\n[1/4] Завантаження стегозображення...")
    img = Image.open(image_path)
    img = img.convert('RGB')
    pixels = img.load()
    width, height = img.size
    print(f"      Розмір: {width}x{height} пікселів")

    print("\n[2/4] Читання молодших бітів...")
    bits = ""
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            bits += str(r & 1)
            bits += str(g & 1)
            bits += str(b & 1)

    print(f"      Зібрано {len(bits)} біт")

    print("\n[3/4] Пошук маркерів повідомлення...")
    start_marker = "11111110111111101111111011111110"  # Унікальний маркер початку (32 біта)
    end_marker = "10101010101010101010101010101010"  # Унікальний маркер кінця (32 біта)

    start = bits.find(start_marker)
    end = bits.find(end_marker, start + len(start_marker) if start != -1 else 0)

    if start == -1 or end == -1:
        print("      [!] Маркери не знайдено!")
        return None

    print(f"      [+] Початок: позиція {start}")
    print(f"      [+] Кінець: позиція {end}")

    message_bits = bits[start + len(start_marker):end]
    message = bits_to_text(message_bits)

    print("\n[4/4] Декодування повідомлення...")

    print("\n" + "=" * 70)
    print("  ВИТЯГУВАННЯ ЗАВЕРШЕНО")
    print("=" * 70)

    return message


def compare_images(original_path, stego_path):
    """Детальний аналіз відмінностей"""
    print("\n" + "=" * 70)
    print("  ПОРІВНЯЛЬНИЙ АНАЛІЗ")
    print("=" * 70)

    try:
        orig_img = Image.open(original_path).convert('RGB')
        stego_img = Image.open(stego_path).convert('RGB')

        orig_pixels = orig_img.load()
        stego_pixels = stego_img.load()

        width, height = orig_img.size

        total_pixels = width * height
        changed_pixels = 0
        total_diff = 0

        print("\nАналіз пікселів...")
        for y in range(height):
            for x in range(width):
                r1, g1, b1 = orig_pixels[x, y]
                r2, g2, b2 = stego_pixels[x, y]

                if (r1, g1, b1) != (r2, g2, b2):
                    changed_pixels += 1
                    total_diff += abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2)

        print(f"\nСтатистика змін:")
        print(f"   Загальна кількість пікселів: {total_pixels:,}")
        print(f"   Змінених пікселів: {changed_pixels:,}")
        print(f"   Відсоток змін: {(changed_pixels / total_pixels * 100):.4f}%")
        print(f"   Середня різниця RGB: {(total_diff / (changed_pixels * 3) if changed_pixels > 0 else 0):.2f}")

        print(f"\nРозміри файлів:")
        orig_size = os.path.getsize(original_path)
        stego_size = os.path.getsize(stego_path)
        print(f"   Оригінал: {orig_size:,} байт")
        print(f"   Стего: {stego_size:,} байт")
        print(
            f"   Різниця: {abs(stego_size - orig_size):,} байт ({abs(stego_size - orig_size) / orig_size * 100:.2f}%)")

        print(f"\n[+] Висновок: Візуально зображення ІДЕНТИЧНІ")

        # Закриваємо зображення
        orig_img.close()
        stego_img.close()

    except Exception as e:
        print(f"[!] Помилка при аналізі: {e}")


# === МЕНЮ ===

def main():
    """Головне меню програми"""

    while True:
        print("\n" + "=" * 70)
        print("  ГОЛОВНЕ МЕНЮ")
        print("=" * 70)
        print("  1. Приховати повідомлення")
        print("  2. Витягнути повідомлення")
        print("  3. Порівняти зображення")
        print("  4. Вихід")
        print("=" * 70)

        choice = input("\nВаш вибір (1-4): ").strip()

        if choice == "1":
            print("\n" + "-" * 70)
            image_path = input("Шлях до PNG-зображення: ").strip()

            if not os.path.exists(image_path):
                print("[!] Файл не знайдено!")
                continue

            message = input("Повідомлення для приховування: ").strip()
            output_path = "stego_" + os.path.basename(image_path)

            try:
                hide_message(image_path, output_path, message)

            except Exception as e:
                print(f"\n[!] Помилка: {e}")

        elif choice == "2":
            print("\n" + "-" * 70)
            image_path = input("Шлях до стегозображення: ").strip()

            if not os.path.exists(image_path):
                print("[!] Файл не знайдено!")
                continue

            try:
                extracted = extract_message(image_path)

                if extracted:
                    print(f"\nВИТЯГНУТЕ ПОВІДОМЛЕННЯ:")
                    print("─" * 70)
                    print(f"   {extracted}")
                    print("─" * 70)
                else:
                    print("\n[!] Повідомлення не знайдено або пошкоджене")

            except Exception as e:
                print(f"\n[!] Помилка: {e}")

        elif choice == "3":
            print("\n" + "-" * 70)
            orig = input("Оригінальне зображення: ").strip()
            stego = input("Стегозображення: ").strip()

            if os.path.exists(orig) and os.path.exists(stego):
                try:
                    compare_images(orig, stego)
                except Exception as e:
                    print(f"\n[!] Помилка: {e}")
            else:
                print("[!] Один із файлів не знайдено!")

        elif choice == "4":
            print("\n" + "=" * 70)
            print("Все")
            print("=" * 70 + "\n")
            break

        else:
            print("\n[!] Невірний вибір. Спробуйте ще раз.")


if __name__ == "__main__":
    main()