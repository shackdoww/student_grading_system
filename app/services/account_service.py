"""Local authentication. Passwords and bearer tokens never appear in listings."""
import base64
import hashlib
import hmac
import re
import secrets
from uuid import uuid4

from psycopg.rows import dict_row
from app.database.connection import get_connection


ROLES = {'admin': 'Admin', 'dean': 'College Dean', 'teacher': 'Teacher', 'registrar': 'Registrar'}


def derive(password, salt):
    return hashlib.scrypt(password.encode('utf-8'), salt=salt, n=2**14, r=8, p=5, dklen=32, maxmem=64*1024*1024)


def hash_password(password):
    if not 15 <= len(password) <= 128:
        raise ValueError('Use a password or passphrase of 15–128 characters.')
    salt = secrets.token_bytes(16)
    return 'scrypt$' + base64.b64encode(salt).decode() + '$' + base64.b64encode(derive(password, salt)).decode()


def verify_password(password, encoded):
    if len(password) > 128:
        return False
    try:
        algorithm, salt, expected = encoded.split('$')
        if algorithm != 'scrypt':
            return False
        return hmac.compare_digest(derive(password, base64.b64decode(salt)), base64.b64decode(expected))
    except (ValueError, TypeError):
        return False


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


class AccountService:
    def __init__(self, connection_factory=None):
        self.connect = connection_factory or get_connection

    def needs_setup(self):
        with self.connect() as connection:
            return connection.execute('SELECT NOT EXISTS(SELECT 1 FROM user_accounts)').fetchone()[0]

    def resolve(self, token, cursor=None):
        if not token:
            raise PermissionError('Sign in to continue.')
        if cursor is None:
            with self.connect() as connection:
                with connection.cursor(row_factory=dict_row) as own_cursor:
                    return self.resolve(token, own_cursor)
        cursor.execute('''SELECT u.user_id,u.username,u.full_name,u.role,u.teacher_id
            FROM account_sessions s JOIN user_accounts u ON u.user_id=s.user_id
            WHERE s.token_hash=%s AND s.expires_at>CURRENT_TIMESTAMP AND u.active''', (token_hash(token),))
        account = cursor.fetchone()
        if not account:
            raise PermissionError('Your session expired or your account was disabled. Sign in again.')
        return account

    def require_admin(self, token, cursor):
        account = self.resolve(token, cursor)
        if account['role'] != 'admin':
            raise PermissionError('Only an Admin can manage accounts and delete records.')
        return account

    def create_account(self, username, full_name, password, role, teacher_id=None, token=None, first_admin=False):
        username = username.strip().lower()
        if not re.fullmatch(r'[a-z0-9][a-z0-9_.-]{2,79}', username):
            raise ValueError('Username must contain 3–80 letters, digits, dots, underscores or hyphens.')
        if not 1 <= len(full_name.strip()) <= 160 or role not in ROLES:
            raise ValueError('A name and valid role are required.')
        if (role == 'teacher') != bool(teacher_id):
            raise ValueError('Teacher accounts require a teacher record; other roles must not link one.')
        encoded = hash_password(password)
        user_id = uuid4()
        with self.connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute('LOCK TABLE user_accounts IN EXCLUSIVE MODE')
                if first_admin:
                    cursor.execute('SELECT 1 FROM user_accounts LIMIT 1')
                    if cursor.fetchone() or role != 'admin':
                        raise PermissionError('Initial setup is already complete.')
                    actor = user_id
                else:
                    actor = self.require_admin(token, cursor)['user_id']
                cursor.execute('''INSERT INTO user_accounts
                    (user_id,username,full_name,password_hash,role,teacher_id) VALUES (%s,%s,%s,%s,%s,%s)''',
                    (user_id, username, full_name.strip(), encoded, role, teacher_id))
                cursor.execute('INSERT INTO security_events(actor_id,action,target) VALUES (%s,%s,%s)',
                               (actor, 'account.created', str(user_id)))
        return user_id

    def authenticate(self, username, password):
        if len(password) > 128 or len(username) > 80:
            raise ValueError('Sign-in failed. Check your credentials, or try later if the account is locked.')
        token = secrets.token_urlsafe(48)
        accepted = False
        with self.connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute('''SELECT *, locked_until > CURRENT_TIMESTAMP AS locked
                    FROM user_accounts WHERE username=%s FOR UPDATE''', (username.strip().lower(),))
                user = cursor.fetchone()
                valid = verify_password(password, user['password_hash']) if user else hmac.compare_digest(derive(password[:128], bytes(16)), bytes(32))
                if user and valid and user['active'] and not user['locked']:
                    cursor.execute('UPDATE user_accounts SET failed_attempts=0,locked_until=NULL WHERE user_id=%s', (user['user_id'],))
                    cursor.execute('DELETE FROM account_sessions WHERE expires_at<=CURRENT_TIMESTAMP')
                    cursor.execute("INSERT INTO account_sessions VALUES (%s,%s,CURRENT_TIMESTAMP+INTERVAL '8 hours')", (token_hash(token), user['user_id']))
                    accepted = True
                elif user and not user['locked']:
                    cursor.execute("""UPDATE user_accounts SET failed_attempts=CASE WHEN failed_attempts>=4 THEN 0 ELSE failed_attempts+1 END,
                        locked_until=CASE WHEN failed_attempts>=4 THEN CURRENT_TIMESTAMP+INTERVAL '15 minutes' ELSE NULL END WHERE user_id=%s""", (user['user_id'],))
        if not accepted:
            raise ValueError('Sign-in failed. Check your credentials, or try later if the account is locked.')
        return token

    def list_accounts(self, token):
        with self.connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                self.require_admin(token, cursor)
                cursor.execute('SELECT user_id,username,full_name,role,teacher_id,active FROM user_accounts ORDER BY username')
                return cursor.fetchall()

    def set_active(self, token, user_id, active):
        with self.connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute('LOCK TABLE user_accounts IN EXCLUSIVE MODE')
                actor = self.require_admin(token, cursor)
                cursor.execute('SELECT role,active FROM user_accounts WHERE user_id=%s', (user_id,))
                target = cursor.fetchone()
                if not target:
                    raise ValueError('Account not found.')
                if not active and target['role'] == 'admin' and target['active']:
                    cursor.execute("SELECT count(*) AS total FROM user_accounts WHERE role='admin' AND active")
                    if cursor.fetchone()['total'] <= 1:
                        raise ValueError('The last active Admin cannot be disabled.')
                if str(actor['user_id']) == str(user_id) and not active:
                    raise ValueError('You cannot disable your own account.')
                cursor.execute('UPDATE user_accounts SET active=%s WHERE user_id=%s', (active, user_id))
                if not active:
                    cursor.execute('DELETE FROM account_sessions WHERE user_id=%s', (user_id,))
                cursor.execute('INSERT INTO security_events(actor_id,action,target) VALUES (%s,%s,%s)',
                               (actor['user_id'], 'account.enabled' if active else 'account.disabled', str(user_id)))

    def logout(self, token):
        with self.connect() as connection:
            connection.execute('DELETE FROM account_sessions WHERE token_hash=%s', (token_hash(token),))

    def change_role(self, token, user_id, role, teacher_id=None):
        if role not in ROLES or (role == 'teacher') != bool(teacher_id):
            raise ValueError('Choose a valid role and link a teacher record only for Teacher accounts.')
        with self.connect() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute('LOCK TABLE user_accounts IN EXCLUSIVE MODE')
                actor = self.require_admin(token, cursor)
                if str(actor['user_id']) == str(user_id):
                    raise ValueError('Another Admin must change your own role.')
                cursor.execute('SELECT role,active FROM user_accounts WHERE user_id=%s', (user_id,))
                target = cursor.fetchone()
                if not target:
                    raise ValueError('Account not found.')
                if target['role'] == 'admin' and target['active'] and role != 'admin':
                    cursor.execute("SELECT count(*) AS total FROM user_accounts WHERE role='admin' AND active")
                    if cursor.fetchone()['total'] <= 1:
                        raise ValueError('The last active Admin cannot be demoted.')
                cursor.execute('UPDATE user_accounts SET role=%s,teacher_id=%s WHERE user_id=%s', (role, teacher_id, user_id))
                cursor.execute('DELETE FROM account_sessions WHERE user_id=%s', (user_id,))
                cursor.execute('INSERT INTO security_events(actor_id,action,target) VALUES (%s,%s,%s)',
                               (actor['user_id'], 'account.role_changed', str(user_id)))
