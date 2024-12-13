# Login and Filter Utilities

Цей репозиторій містить утиліти для автоматичного логіну на веб-сайти з обходом Cloudflare та фільтрації паролів за заданим шаблоном.

## Встановлення

Щоб встановити необхідні залежності на чистій системі Debian, виконайте наступні дії:

1. Оновіть списки пакетів і встановіть pip:

    ```sh
    sudo apt update
    sudo apt install python3-pip -y
    ```

2. Встановіть пакети для `pyopencl` та інші необхідні пакети:

    ```sh
    sudo apt install -y ocl-icd-libopencl1 opencl-headers clinfo
    sudo apt install -y build-essential python3-dev python3-pip
    sudo apt install -y ocl-icd-opencl-dev
    sudo apt install -y libffi-dev libssl-dev
    sudo apt install -y tor
    ```

3. Клонування репозиторію та встановлення залежностей:

    ```sh
    git clone https://github.com/Bobovychb/login-and-filter-utils.git
    cd login-and-filter-utils
    ```

4. Встановіть залежності для кожного проекту:

    Для фільтрації паролів:

    ```sh
    pip3 install -r requirements_filter.txt
    ```

    Для автоматичного логіну:

    ```sh
    pip3 install -r requirements_autologin.txt
    ```

## Використання

### Утиліта для автоматичного логіну

Ця утиліта використовує Selenium для автоматичного логіну на веб-сайти з обходом Cloudflare та підтримкою Tor мережі.

#### Приклади використання

1. Автоматичний логін без використання Tor:

    ```sh
    python autologin.py -l LOGIN -p PASSWORD_FILE --url https://google.com
    ```

2. Автоматичний логін з використанням Tor:

    ```sh
    python autologin.py --tor -l LOGIN -p PASSWORD_FILE --url https://google.com
    ```

### Утиліта для фільтрації паролів

Ця утиліта дозволяє фільтрувати паролі за заданим шаблоном з використанням CPU або GPU.

#### Приклади використання

1. Фільтрація паролів з використанням CPU:

    ```sh
    python filter.py ваш_файл_з_паролями -p шаблон_пароля
    ```

2. Фільтрація паролів з використанням GPU:

    ```sh
    python filter.py ваш_файл_з_паролями -p шаблон_пароля -g
    ```

## Додаткові параметри

- `-l`, `--login` – Логін користувача (обов'язково для autologin.py)
- `-p`, `--password-file` – Файл з паролями (обов'язково для обох утиліт)
- `--url` – URL сторінки логіну (обов'язково для autologin.py)
- `--cloudflare` – Режим обходу Cloudflare (для autologin.py)
- `--tor` – Використовувати Tor мережу для автологіну (для autologin.py)
- `--attempts` – Кількість спроб для кожного пароля (для autologin.py)
- `--resume` – Відновити з останнього збереженого стану (для autologin.py)
- `-g`, `--gpu` – Використовувати GPU для фільтрації паролів (для filter.py)
- `-o`, `--output` – Шлях для збереження відфільтрованих паролів (для filter.py)

## Важлива примітка

Ці утиліти призначені для використання у легальних цілях, таких як тестування безпеки ваших власних систем або систем, на які ви маєте відповідний дозвіл. Автор не несе відповідальності за будь-яку шкоду, спричинену в результаті неправомірного використання цих утиліт.

## Внесок

Якщо ви хочете внести свій внесок у цей проект, будь ласка, відкрийте pull request або створіть issue для обговорення ваших змін.

## Ліцензія

Цей проект ліцензований під MIT License.
