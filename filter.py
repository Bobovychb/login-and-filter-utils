import sys
import os
import re
import numpy as np
import pyopencl as cl

def parse_pattern(pattern):
    length = len(pattern)
    regex_pattern = pattern.replace('%', '.')
    return regex_pattern, length

def filter_passwords_cpu(input_file, output_file, regex_pattern, length):
    filtered_passwords = []

    try:
        with open(input_file, "r") as infile:
            for line in infile:
                password = line.strip()
                if len(password) == length and re.match(regex_pattern, password):
                    filtered_passwords.append(password)

        with open(output_file, "w") as outfile:
            outfile.write("\n".join(filtered_passwords))

        print(f"Знайдено {len(filtered_passwords)} паролів, які відповідають критеріям.")
        return len(filtered_passwords)
    except FileNotFoundError:
        print("Помилка: Файл для читання не знайдено.")
        return 0
    except IsADirectoryError:
        print("Помилка: Вказано каталог замість файлу для збереження.")
        return 0
    except Exception as e:
        print(f"Невідома помилка: {e}")
        return 0

def filter_passwords_gpu(input_file, output_file, regex_pattern, length):
    try:
        platform = cl.get_platforms()[0]
        device = platform.get_devices()[0]
        context = cl.Context([device])
        queue = cl.CommandQueue(context)

        with open(input_file, "r") as infile:
            passwords = infile.read().splitlines()

        # Підготовка даних для GPU
        passwords_np = np.array(passwords, dtype=np.object_)
        passwords_flat = ''.join([p.ljust(length) for p in passwords]).encode('utf-8')
        buffer = cl.Buffer(context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=passwords_flat)

        regex_pattern = regex_pattern.encode('utf-8')
        regex_buffer = cl.Buffer(context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=regex_pattern)

        kernel_code = """
        __kernel void filter(
            __global const char *passwords,
            __global char *results,
            __global const char *regex_pattern,
            const int length
        ) {
            int gid = get_global_id(0);
            const __global char *password = passwords + gid * length;
            
            // Initialize result to 1 (valid)
            results[gid] = 1;

            // Check each character against regex pattern
            for (int i = 0; i < length; ++i) {
                if (regex_pattern[i] != '.' && password[i] != regex_pattern[i]) {
                    results[gid] = 0;
                    break;
                }
            }
        }
        """
        program = cl.Program(context, kernel_code).build()
        result_np = np.zeros(len(passwords), dtype=np.uint8)
        result_buffer = cl.Buffer(context, cl.mem_flags.WRITE_ONLY, result_np.nbytes)

        kernel = program.filter
        kernel(queue, (len(passwords),), None, buffer, result_buffer, regex_buffer, np.int32(length))

        cl.enqueue_copy(queue, result_np, result_buffer)

        filtered_passwords = [pw for pw, valid in zip(passwords, result_np) if valid]
        with open(output_file, "w") as outfile:
            outfile.write("\n".join(filtered_passwords))

        print(f"Знайдено {len(filtered_passwords)} паролів, які відповідають критеріям.")
        return len(filtered_passwords)

    except Exception as e:
        print(f"Помилка GPU-фільтрації: {e}")
        return 0

def print_help():
    help_message = """
Використання: python filter.py [опції]

Опції:
  input_file          Шлях до файлу з паролями.
  -p, --pattern       Шаблон пароля (наприклад, A%%%fd).
  -o, --output        Шлях для збереження результату (за замовчуванням: filtered_passwords_<pattern>.txt).
  -g, --gpu           Використовувати GPU для фільтрації.
  -h, --help          Показати це повідомлення і вийти.
"""
    print(help_message)

def main():
    if "-h" in sys.argv or "--help" in sys.argv:
        print_help()
        sys.exit(0)

    if len(sys.argv) < 3:
        print("Недостатньо аргументів.")
        print_help()
        sys.exit(1)

    input_file = sys.argv[1]
    pattern = None
    output_file = None
    use_gpu = False

    try:
        for i in range(2, len(sys.argv)):
            if sys.argv[i] in ("-p", "--pattern"):
                pattern = sys.argv[i + 1]
            elif sys.argv[i] in ("-o", "--output"):
                output_file = sys.argv[i + 1]
            elif sys.argv[i] in ("-g", "--gpu"):
                use_gpu = True

        if not pattern:
            raise ValueError("Шаблон пароля обов'язковий. Використовуйте -p або --pattern.")

        regex_pattern, length = parse_pattern(pattern)
        output_file = output_file or f"filtered_passwords_{pattern.replace('%', 'X')}.txt"

        file_size_mb = os.path.getsize(input_file) / (1024 * 1024)

        if use_gpu or file_size_mb > 100:
            print("Використовуємо GPU для фільтрації...")
            filter_passwords_gpu(input_file, output_file, regex_pattern, length)
        else:
            print("Використовуємо CPU для фільтрації...")
            filter_passwords_cpu(input_file, output_file, regex_pattern, length)

    except Exception as e:
        print(f"Помилка: {e}")
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
