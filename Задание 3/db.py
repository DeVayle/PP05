import psycopg2
from psycopg2 import extras

class DBManager:
    def __init__(self):
        self.connection_params = {
            "dbname": "production_db",
            "user": "postgres",
            "password": "123",
            "host": "localhost",
            "port": "5432"
        }

    def get_connection(self):
        try:
            return psycopg2.connect(**self.connection_params)
        except Exception as e:
            print(f"Ошибка подключения к БД: {e}")
            return None

    def get_all_users(self):
        conn = self.get_connection()
        if not conn: return []
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                query = """
                    SELECT u.id, u.username, u.password, u.f, u.i, u.o, 
                           u.role_id, r.name as role_name, u.is_blocked 
                    FROM users u 
                    JOIN roles r ON u.role_id = r.id
                    ORDER BY u.id
                """
                cur.execute(query)
                return cur.fetchall()
        finally:
            conn.close()

    def get_roles(self):
        conn = self.get_connection()
        if not conn: return []
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute("SELECT id, name FROM roles")
                return cur.fetchall()
        finally:
            conn.close()

    def add_user(self, username, password, f, i, o, role_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cur.fetchone():
                    return False, f"Пользователь с логином '{username}' уже существует!"
                
                cur.execute("""
                    INSERT INTO users (username, password, f, i, o, role_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (username, password, f, i, o, role_id))
                conn.commit()
                return True, "Пользователь успешно добавлен"
        except Exception as e:
            return False, f"Ошибка БД: {e}"
        finally:
            conn.close()

    def update_user(self, user_id, username, password, f, i, o, role_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                query = """
                    UPDATE users 
                    SET username=%s, password=%s, f=%s, i=%s, o=%s, role_id=%s
                    WHERE id=%s
                """
                cur.execute(query, (username, password, f, i, o, role_id, user_id))
                conn.commit()
                return True, "Данные пользователя успешно обновлены"
        except Exception as e:
            return False, f"Ошибка при обновлении: {e}"
        finally:
            conn.close()

    def unblock_user(self, user_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET is_blocked = FALSE, failed_login_attempts = 0 WHERE id = %s", (user_id,))
                conn.commit()
                return True
        except:
            return False
        finally:
            conn.close()

    def increment_failed_attempts(self, login):
        conn = self.get_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET failed_login_attempts = failed_login_attempts + 1 WHERE username = %s", (login,))
                cur.execute("SELECT failed_login_attempts FROM users WHERE username = %s", (login,))
                attempts = cur.fetchone()
                if attempts and attempts[0] >= 3:
                    cur.execute("UPDATE users SET is_blocked = TRUE WHERE username = %s", (login,))
                conn.commit()
        finally:
            conn.close()

    def check_auth(self, login, password):
        conn = self.get_connection()
        if not conn: return False, "Ошибка БД", None, False
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute("SELECT u.*, r.name as role_name FROM users u JOIN roles r ON u.role_id = r.id WHERE u.username = %s", (login,))
                user = cur.fetchone()
                if not user:
                    return False, "Вы ввели неверный логин или пароль...", None, False
                if user['is_blocked']:
                    return False, "Вы заблокированы. Обратитесь к администратору", None, True
                if user['password'] == password:
                    cur.execute("UPDATE users SET failed_login_attempts = 0 WHERE id = %s", (user['id'],))
                    conn.commit()
                    return True, "Вы успешно авторизовались", user['role_name'], False
                else:
                    self.increment_failed_attempts(login)
                    cur.execute("SELECT is_blocked FROM users WHERE username = %s", (login,))
                    if cur.fetchone()[0]:
                        return False, "Вы заблокированы. Обратитесь к администратору", None, True
                    return False, "Вы ввели неверный логин или пароль...", None, False
        finally:
            conn.close()

    def get_products(self):
        conn = self.get_connection()
        if not conn: return []
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:

                try:
                    cur.execute("SELECT id, name, n_type, unit, code FROM products ORDER BY id")
                    return cur.fetchall()
                except:
                    return [
                        {"id": 1, "name": "Диван 'Уют'", "n_type": 1, "unit": 2, "code": "DNG-001"},
                        {"id": 2, "name": "Стол обеденный", "n_type": 1, "unit": 2, "code": "DNG-002"},
                        {"id": 3, "name": "Шкаф-купе", "n_type": 1, "unit": 2, "code": "DNG-003"},
                    ]
        finally:
            conn.close()