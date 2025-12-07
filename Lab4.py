import hashlib
import os

MODULO = 1000007
MULT = 7
INV_MULT = 857149


def hash_document(filename):
    with open(filename, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def generate_private_key(name, birthdate, secret):
    data = name + birthdate + secret
    return int(hashlib.sha256(data.encode()).hexdigest(), 16) % MODULO


def generate_public_key(private_key):
    return (private_key * MULT) % MODULO


def recover_private_from_public(public_key):
    return (public_key * INV_MULT) % MODULO


def sign_document(doc_hash, private_key):
    return int(doc_hash, 16) ^ private_key


def verify_signature(signature_file, doc_file, public_key):
    if not os.path.exists(signature_file) or not os.path.exists(doc_file):
        print("Файл документа або підпису не знайдено.")
        return False

    with open(signature_file, "r") as f:
        signature = int(f.read().strip())

    private_key = recover_private_from_public(public_key)
    doc_hash = hash_document(doc_file)
    decrypted = signature ^ private_key
    return decrypted == int(doc_hash, 16)


def create_document(name):
    filename = f"document_{name}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Документ користувача {name}.\n")
        f.write("Використовується для демонстрації цифрового підпису.")
    return filename


def main():
    global name, private_key, public_key, doc_file, signature_file

    while True:
        print("\n--- МЕНЮ ---")
        print("1. Тестовий приклад")
        print("2. Створити ключі")
        print("3. Створити документ")
        print("4. Підписати документ")
        print("5. Перевірити підпис")
        print("6. Підробити документ")
        print("7. Вихід")

        choice = input("Оберіть дію: ")

        if choice == "1":
            name = "Kovalenko"
            birthdate = "12071998"
            secret = "crypto123"

            private_key = generate_private_key(name, birthdate, secret)
            public_key = generate_public_key(private_key)

            doc_file = create_document(name)
            signature_file = f"signature_{name}.sig"

            print(f"\nПриватний ключ: {private_key}")
            print(f"Публічний ключ: {public_key}")
            print(f"Документ: {doc_file}")

        elif choice == "2":
            name = input("Прізвище: ")
            birthdate = input("Дата народження (напр. 15031995): ")
            secret = input("Секретне слово: ")

            private_key = generate_private_key(name, birthdate, secret)
            public_key = generate_public_key(private_key)
            signature_file = f"signature_{name}.sig"

            print("\nКлючі створено.")
            print("Публічний ключ:", public_key)

        elif choice == "3":
            if "name" not in globals():
                print("Спочатку створіть ключі.")
                continue

            doc_file = create_document(name)
            print("Документ створено:", doc_file)

        elif choice == "4":
            if "doc_file" not in globals():
                print("Спочатку створіть документ.")
                continue

            doc_hash = hash_document(doc_file)
            signature = sign_document(doc_hash, private_key)

            with open(signature_file, "w") as f:
                f.write(str(signature))

            print("Документ підписано.")
            print("Підпис:", signature)

        elif choice == "5":
            doc_to_check = input("Документ: ")
            sig_to_check = input("Файл підпису: ")

            valid = verify_signature(sig_to_check, doc_to_check, public_key)
            print("\nПІДПИС ДІЙСНИЙ" if valid else "\nПІДПИС НЕДІЙСНИЙ або документ змінено")

        elif choice == "6":
            if "doc_file" not in globals():
                print("Немає документа.")
                continue

            with open(doc_file, "a", encoding="utf-8") as f:
                f.write("\nПІДРОБКА.")

            print("Документ змінено (імітація підробки).")

        elif choice == "7":
            print("Вихід.")
            break

        else:
            print("Невірна команда.")


if __name__ == "__main__":
    main()
