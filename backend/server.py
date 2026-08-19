import json
import sqlite3
import hashlib
import hmac
import requests
import secrets
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from pathlib import Path

HOST = "0.0.0.0"
PORT = int(__import__("os").environ.get("PORT", "8000"))

DB_PATH = __import__("os").environ.get("GODO_AI_DB_PATH", "backend/database/godo_ai.db")

IDENTITY_HASH_SECRET = __import__("os").environ.get("GODO_AI_IDENTITY_SECRET", "")


RESEND_API_KEY = __import__("os").environ.get("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = __import__("os").environ.get(
    "RESEND_FROM_EMAIL",
    "onboarding@resend.dev"
)


def send_verification_email(destination, code):
    if not RESEND_API_KEY:
        raise RuntimeError(
            "RESEND_API_KEY is not configured."
        )

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "from": RESEND_FROM_EMAIL,
            "to": [destination],
            "subject": "GODO AI Email Verification",
            "html": f"""
                <h2>GODO AI Email Verification</h2>
                <p>Your verification code is:</p>
                <h1>{code}</h1>
                <p>This code expires in 15 minutes.</p>
                <p>If you did not create this account, you can ignore this email.</p>
            """
        },
        timeout=15
    )

    if not response.ok:
        raise RuntimeError(
            f"Resend email failed: HTTP {response.status_code}"
        )

    return True




def get_db():
    db_path = Path(DB_PATH)

    if db_path.parent:
        db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            role TEXT NOT NULL DEFAULT 'user'
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


    conn.execute("""
        CREATE TABLE IF NOT EXISTS pending_registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone_number TEXT,
            country TEXT NOT NULL,
            region TEXT NOT NULL,
            city TEXT NOT NULL,
            physical_address TEXT,
            identity_hash TEXT NOT NULL,
            email_verified INTEGER NOT NULL DEFAULT 0,
            phone_verified INTEGER NOT NULL DEFAULT 0,
            password_hash TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)


    conn.execute("""
        CREATE TABLE IF NOT EXISTS pending_verification_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registration_id INTEGER NOT NULL,
            channel TEXT NOT NULL,
            destination TEXT NOT NULL,
            code_hash TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            used INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (registration_id)
                REFERENCES pending_registrations(id)
        )
    """)

    # ---------------------------------------------------------
    # Database migrations for existing installations.
    # CREATE TABLE IF NOT EXISTS does not modify an existing
    # table, so older databases need missing columns added.
    # ---------------------------------------------------------

    def add_column_if_missing(table, column, definition):
        columns = {
            row["name"]
            for row in conn.execute(
                f"PRAGMA table_info({table})"
            ).fetchall()
        }

        if column not in columns:
            conn.execute(
                f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
            )

    # Existing users table migration.
    add_column_if_missing(
        "users",
        "email_verified",
        "INTEGER NOT NULL DEFAULT 0"
    )

    add_column_if_missing(
        "users",
        "phone_number",
        "TEXT"
    )

    add_column_if_missing(
        "users",
        "phone_verified",
        "INTEGER NOT NULL DEFAULT 0"
    )

    add_column_if_missing(
        "users",
        "country",
        "TEXT"
    )

    add_column_if_missing(
        "users",
        "region",
        "TEXT"
    )

    add_column_if_missing(
        "users",
        "city",
        "TEXT"
    )

    add_column_if_missing(
        "users",
        "identity_hash",
        "TEXT"
    )

    add_column_if_missing(
        "users",
        "updated_at",
        "TEXT"
    )

    conn.commit()
    conn.close()


def hash_identity(identity_number):
    normalized = "".join(
        str(identity_number).strip().upper().split()
    )

    if not normalized:
        return None

    if not IDENTITY_HASH_SECRET:
        raise RuntimeError(
            "GODO_AI_IDENTITY_SECRET is not configured."
        )

    return hmac.new(
        IDENTITY_HASH_SECRET.encode("utf-8"),
        normalized.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def hash_password(password):
    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        200000
    )

    return salt.hex() + ":" + password_hash.hex()


def verify_password(password, stored_hash):
    try:
        salt_hex, hash_hex = stored_hash.split(":", 1)

        salt = bytes.fromhex(salt_hex)

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            200000
        )

        return secrets.compare_digest(
            password_hash.hex(),
            hash_hex
        )

    except ValueError:
        return False


def hash_reset_token(token):
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def utc_now():
    return datetime.now(timezone.utc)


def reset_token_expiry(minutes=15):
    return (
        utc_now() + timedelta(minutes=minutes)
    ).isoformat()


class AuthHandler(BaseHTTPRequestHandler):

    def send_json(self, status, data):

        body = json.dumps(data).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json"
        )


        self.send_header(
            "Access-Control-Allow-Origin",
            "https://iamlungs7.github.io"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.end_headers()

        self.wfile.write(body)


    def read_json(self):

        length = int(
            self.headers.get("Content-Length", 0)
        )

        body = self.rfile.read(length)

        return json.loads(
            body.decode("utf-8")
        )

    def do_OPTIONS(self):

        self.send_response(204)

        self.send_header(
            "Access-Control-Allow-Origin",
            "https://iamlungs7.github.io"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization"
        )

        self.end_headers()


    def get_session_user(self):

        auth_header = self.headers.get(
            "Authorization",
            ""
        )

        if not auth_header.startswith("Bearer "):

            return None

        token = auth_header[7:].strip()

        if not token:

            return None

        conn = get_db()

        user = conn.execute(
            """
            SELECT
                users.id,
                users.full_name,
                users.email,
                users.role
            FROM sessions
            JOIN users
                ON users.id = sessions.user_id
            WHERE sessions.token = ?
            """,
            (token,)
        ).fetchone()

        conn.close()

        return user

    def require_master(self):
        user = self.get_session_user()

        if not user:
            self.send_json(
                401,
                {
                    "authenticated": False,
                    "error": "Authentication required."
                }
            )
            return None

        if user["role"] != "master":
            self.send_json(
                403,
                {
                    "authenticated": True,
                    "authorized": False,
                    "error": "Master account required."
                }
            )
            return None

        return user


    def do_GET(self):
        path = urlparse(
            self.path
        ).path

        if path == "/api/health":

            self.send_json(
                200,
                {
                    "status": "online",
                    "service": "GODO AI Auth Backend"
                }
            )

            return

        if path == "/api/session":

            user = self.get_session_user()

            if not user:

                self.send_json(
                    401,
                    {
                        "authenticated": False,
                        "error": "Invalid or missing session."
                    }
                )

                return

            self.send_json(
                200,
                {
                    "authenticated": True,
                    "user": {
                        "id": user["id"],
                        "full_name": user["full_name"],
                        "email": user["email"],
                        "role": user["role"]
                    }
                }
            )

            return

        if path == "/api/master/overview":

            master = self.require_master()

            if not master:
                return

            conn = get_db()

            users = conn.execute(
                """
                SELECT
                    id,
                    full_name,
                    email,
                    role,
                    created_at
                FROM users
                ORDER BY id ASC
                """
            ).fetchall()

            session_count = conn.execute(
                "SELECT COUNT(*) FROM sessions"
            ).fetchone()[0]

            user_count = conn.execute(
                "SELECT COUNT(*) FROM users"
            ).fetchone()[0]

            conn.close()

            self.send_json(
                200,
                {
                    "success": True,
                    "master": {
                        "id": master["id"],
                        "full_name": master["full_name"],
                        "email": master["email"],
                        "role": master["role"]
                    },
                    "overview": {
                        "total_users": user_count,
                        "active_sessions": session_count
                    },
                    "users": [
                        {
                            "id": user["id"],
                            "full_name": user["full_name"],
                            "email": user["email"],
                            "role": user["role"],
                            "created_at": user["created_at"]
                        }
                        for user in users
                    ]
                }
            )

            return


        self.send_json(
            404,
            {
                "error": "Endpoint not found"
            }
        )


    def do_POST(self):

        path = urlparse(
            self.path
        ).path

        try:
            data = self.read_json()

        except Exception:

            self.send_json(
                400,
                {
                    "error": "Invalid JSON"
                }
            )

            return


        if path == "/api/forgot-password":

            self.forgot_password(data)

            return


        if path == "/api/reset-password":

            self.reset_password(data)

            return


        if path == "/api/register/start":

            self.register_start(data)

            return


        if path == "/api/register/verify-email":

            self.verify_pending_email(data)

            return


        if path == "/api/register/verify-phone":

            self.verify_pending_phone(data)

            return


        if path == "/api/register/complete":

            self.complete_registration(data)

            return


        if path == "/api/register":

            self.register(data)

            return


        if path == "/api/login":

            self.login(data)

            return


        self.send_json(
            404,
            {
                "error": "Endpoint not found"
            }
        )


    def forgot_password(self, data):

        email = str(
            data.get("email", "")
        ).strip().lower()

        # Always return the same response so the endpoint
        # does not reveal whether an email exists.
        generic_response = {
            "success": True,
            "message": (
                "If the account exists, a password reset "
                "request has been created."
            )
        }

        if not email:
            self.send_json(
                200,
                generic_response
            )
            return

        conn = get_db()

        user = conn.execute(
            """
            SELECT id, email
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if not user:
            conn.close()

            self.send_json(
                200,
                generic_response
            )
            return

        # Invalidate previous unused reset tokens.
        conn.execute(
            """
            UPDATE password_reset_tokens
            SET used = 1
            WHERE user_id = ?
              AND used = 0
            """,
            (user["id"],)
        )

        raw_token = secrets.token_urlsafe(32)

        token_hash = hash_reset_token(
            raw_token
        )

        expires_at = reset_token_expiry(15)

        conn.execute(
            """
            INSERT INTO password_reset_tokens
            (
                user_id,
                token_hash,
                expires_at,
                used
            )
            VALUES (?, ?, ?, 0)
            """,
            (
                user["id"],
                token_hash,
                expires_at
            )
        )

        conn.commit()
        conn.close()

        # Temporary development response.
        # This will be replaced by email delivery in Step 3.
        response = dict(generic_response)

        response["development_token"] = raw_token

        self.send_json(
            200,
            response
        )


    def reset_password(self, data):

        token = str(
            data.get("token", "")
        ).strip()

        new_password = str(
            data.get("new_password", "")
        )

        if not token or not new_password:

            self.send_json(
                400,
                {
                    "success": False,
                    "error": (
                        "Reset token and new password "
                        "are required."
                    )
                }
            )

            return

        if len(new_password) < 8:

            self.send_json(
                400,
                {
                    "success": False,
                    "error": (
                        "Password must be at least "
                        "8 characters."
                    )
                }
            )

            return

        token_hash = hash_reset_token(
            token
        )

        conn = get_db()

        reset = conn.execute(
            """
            SELECT
                id,
                user_id,
                expires_at,
                used
            FROM password_reset_tokens
            WHERE token_hash = ?
            """,
            (token_hash,)
        ).fetchone()

        if not reset:

            conn.close()

            self.send_json(
                400,
                {
                    "success": False,
                    "error": "Invalid reset token."
                }
            )

            return

        if reset["used"]:

            conn.close()

            self.send_json(
                400,
                {
                    "success": False,
                    "error": "Reset token has already been used."
                }
            )

            return

        try:
            expires_at = datetime.fromisoformat(
                reset["expires_at"]
            )

            if utc_now() >= expires_at:

                conn.execute(
                    """
                    UPDATE password_reset_tokens
                    SET used = 1
                    WHERE id = ?
                    """,
                    (reset["id"],)
                )

                conn.commit()
                conn.close()

                self.send_json(
                    400,
                    {
                        "success": False,
                        "error": "Reset token has expired."
                    }
                )

                return

        except ValueError:

            conn.close()

            self.send_json(
                400,
                {
                    "success": False,
                    "error": "Invalid reset token."
                }
            )

            return

        password_hash = hash_password(
            new_password
        )

        conn.execute(
            """
            UPDATE users
            SET password_hash = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                password_hash,
                reset["user_id"]
            )
        )

        conn.execute(
            """
            UPDATE password_reset_tokens
            SET used = 1
            WHERE id = ?
            """,
            (reset["id"],)
        )

        # Revoke existing sessions after password reset.
        conn.execute(
            """
            DELETE FROM sessions
            WHERE user_id = ?
            """,
            (reset["user_id"],)
        )

        conn.commit()
        conn.close()

        self.send_json(
            200,
            {
                "success": True,
                "message": (
                    "Password reset successful. "
                    "Please login again."
                )
            }
        )


    def create_verification_code(
        self,
        user_id,
        purpose,
        channel,
        destination
    ):
        """
        Create a secure one-time verification code.

        The raw OTP is never stored in the database.
        Only its SHA-256 hash is stored.
        """

        code = f"{secrets.randbelow(1000000):06d}"

        code_hash = hashlib.sha256(
            code.encode("utf-8")
        ).hexdigest()

        expires_at = (
            utc_now() + timedelta(minutes=15)
        ).isoformat()

        conn = get_db()

        # Invalidate previous unused codes
        # for the same verification purpose/channel.
        conn.execute(
            """
            UPDATE verification_codes
            SET used = 1
            WHERE user_id = ?
              AND purpose = ?
              AND channel = ?
              AND used = 0
            """,
            (
                user_id,
                purpose,
                channel
            )
        )

        conn.execute(
            """
            INSERT INTO verification_codes (
                user_id,
                purpose,
                channel,
                destination,
                code_hash,
                expires_at,
                attempts,
                used
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, 0)
            """,
            (
                user_id,
                purpose,
                channel,
                destination,
                code_hash,
                expires_at
            )
        )

        conn.commit()
        conn.close()

        return code


    def verify_code(
        self,
        user_id,
        purpose,
        channel,
        code
    ):
        """
        Verify a one-time code.

        Rules:
        - 6 digits
        - maximum 5 attempts
        - 15 minute expiry
        - one-time use
        """

        code = str(code).strip()

        if not code.isdigit() or len(code) != 6:

            return False, "Invalid verification code."

        code_hash = hashlib.sha256(
            code.encode("utf-8")
        ).hexdigest()

        conn = get_db()

        verification = conn.execute(
            """
            SELECT
                id,
                code_hash,
                expires_at,
                attempts,
                used
            FROM verification_codes
            WHERE user_id = ?
              AND purpose = ?
              AND channel = ?
              AND used = 0
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                user_id,
                purpose,
                channel
            )
        ).fetchone()

        if not verification:

            conn.close()

            return False, "Verification code not found or already used."

        if verification["attempts"] >= 5:

            conn.execute(
                """
                UPDATE verification_codes
                SET used = 1
                WHERE id = ?
                """,
                (verification["id"],)
            )

            conn.commit()
            conn.close()

            return False, "Too many verification attempts."

        try:

            expires_at = datetime.fromisoformat(
                verification["expires_at"]
            )

        except ValueError:

            conn.close()

            return False, "Invalid verification code."

        if utc_now() >= expires_at:

            conn.execute(
                """
                UPDATE verification_codes
                SET used = 1
                WHERE id = ?
                """,
                (verification["id"],)
            )

            conn.commit()
            conn.close()

            return False, "Verification code has expired."

        new_attempts = verification["attempts"] + 1

        if not secrets.compare_digest(
            code_hash,
            verification["code_hash"]
        ):

            conn.execute(
                """
                UPDATE verification_codes
                SET attempts = ?
                WHERE id = ?
                """,
                (
                    new_attempts,
                    verification["id"]
                )
            )

            conn.commit()
            conn.close()

            remaining = 5 - new_attempts

            if remaining <= 0:

                return False, "Too many verification attempts."

            return (
                False,
                f"Invalid verification code. "
                f"{remaining} attempts remaining."
            )

        conn.execute(
            """
            UPDATE verification_codes
            SET used = 1,
                attempts = ?
            WHERE id = ?
            """,
            (
                new_attempts,
                verification["id"]
            )
        )

        conn.commit()
        conn.close()

        return True, "Verification successful."


    def create_pending_verification_code(
        self,
        registration_id,
        channel,
        destination
    ):
        """
        Create a secure one-time OTP for a pending registration.

        The raw OTP is never stored in the database.
        Only its SHA-256 hash is stored.
        """

        code = f"{secrets.randbelow(1000000):06d}"

        code_hash = hashlib.sha256(
            code.encode("utf-8")
        ).hexdigest()

        expires_at = (
            utc_now() + timedelta(minutes=15)
        ).isoformat()

        conn = get_db()

        # Invalidate previous unused OTPs for this
        # registration and verification channel.
        conn.execute(
            """
            UPDATE pending_verification_codes
            SET used = 1
            WHERE registration_id = ?
              AND channel = ?
              AND used = 0
            """,
            (
                registration_id,
                channel
            )
        )

        conn.execute(
            """
            INSERT INTO pending_verification_codes (
                registration_id,
                channel,
                destination,
                code_hash,
                expires_at,
                attempts,
                used
            )
            VALUES (?, ?, ?, ?, ?, 0, 0)
            """,
            (
                registration_id,
                channel,
                destination,
                code_hash,
                expires_at
            )
        )

        conn.commit()
        conn.close()

        return code


    def register_start(self, data):

        full_name = str(
            data.get("full_name", "")
        ).strip()

        surname = str(
            data.get("surname", "")
        ).strip()

        email = str(
            data.get("email", "")
        ).strip().lower()

        phone_number = str(
            data.get("phone_number", "")
        ).strip()

        country = str(
            data.get("country", "")
        ).strip()

        region = str(
            data.get("region", "")
        ).strip()

        city = str(
            data.get("city", "")
        ).strip()

        physical_address = str(
            data.get("physical_address", "")
        ).strip()

        identity_number = str(
            data.get("identity_number", "")
        ).strip()


        if not all([
            full_name,
            surname,
            email,
            phone_number,
            country,
            region,
            city,
            physical_address,
            identity_number
        ]):

            self.send_json(
                400,
                {
                    "error": (
                        "All personal details are required."
                    )
                }
            )

            return


        try:

            identity_hash = hash_identity(
                identity_number
            )

        except RuntimeError as error:

            print(
                "Registration security error:",
                error
            )

            self.send_json(
                500,
                {
                    "error": (
                        "Registration security "
                        "is not configured."
                    )
                }
            )

            return


        conn = get_db()


        existing_email = conn.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()


        if existing_email:

            conn.close()

            self.send_json(
                409,
                {
                    "error": (
                        "An account with this "
                        "email already exists."
                    )
                }
            )

            return


        existing_identity = conn.execute(
            """
            SELECT id
            FROM users
            WHERE identity_hash = ?
            """,
            (identity_hash,)
        ).fetchone()


        if existing_identity:

            conn.close()

            self.send_json(
                409,
                {
                    "error": (
                        "An account with this "
                        "identity already exists."
                    )
                }
            )

            return


        existing_pending = conn.execute(
            """
            SELECT id
            FROM pending_registrations
            WHERE email = ?
            """,
            (email,)
        ).fetchone()


        if existing_pending:

            registration_id = existing_pending["id"]

            conn.execute(
                """
                UPDATE pending_registrations
                SET full_name = ?,
                    phone_number = ?,
                    country = ?,
                    region = ?,
                    city = ?,
                    physical_address = ?,
                    identity_hash = ?,
                    email_verified = 0,
                    phone_verified = 0,
                    password_hash = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    f"{full_name} {surname}",
                    phone_number,
                    country,
                    region,
                    city,
                    physical_address,
                    identity_hash,
                    registration_id
                )
            )

        else:

            cursor = conn.execute(
                """
                INSERT INTO pending_registrations (
                    full_name,
                    email,
                    phone_number,
                    country,
                    region,
                    city,
                    physical_address,
                    identity_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"{full_name} {surname}",
                    email,
                    phone_number,
                    country,
                    region,
                    city,
                    physical_address,
                    identity_hash
                )
            )

            registration_id = cursor.lastrowid


        conn.commit()
        conn.close()


        email_otp = self.create_pending_verification_code(
            registration_id,
            "email",
            email
        )

        phone_otp = self.create_pending_verification_code(
            registration_id,
            "phone",
            phone_number
        )


        try:

            send_verification_email(
                email,
                email_otp
            )

        except Exception as error:

            print(
                "Pending email verification delivery error:",
                error
            )

            self.send_json(
                503,
                {
                    "success": False,
                    "error": (
                        "Registration started, but "
                        "the verification email could "
                        "not be sent. Please try again."
                    )
                }
            )

            return


        self.send_json(
            201,
            {
                "success": True,
                "message": (
                    "Registration started. "
                    "Please verify your email."
                ),
                "registration_id": registration_id,
                "next_step": "email_verification"
            }
        )


    def verify_pending_email(self, data):

        registration_id = data.get("registration_id")

        code = str(
            data.get("code", "")
        ).strip()

        if not registration_id or not code:

            self.send_json(
                400,
                {
                    "error": (
                        "Registration ID and verification code "
                        "are required."
                    )
                }
            )

            return

        try:
            registration_id = int(registration_id)
        except (TypeError, ValueError):

            self.send_json(
                400,
                {
                    "error": "Invalid registration ID."
                }
            )

            return

        conn = get_db()

        registration = conn.execute(
            """
            SELECT id, email, email_verified
            FROM pending_registrations
            WHERE id = ?
            """,
            (registration_id,)
        ).fetchone()

        conn.close()

        if not registration:

            self.send_json(
                404,
                {
                    "error": "Registration could not be found."
                }
            )

            return

        if registration["email_verified"]:

            self.send_json(
                200,
                {
                    "success": True,
                    "email_verified": True,
                    "next_step": "phone"
                }
            )

            return

        ok, message = self.verify_pending_code(
            registration_id,
            "email",
            code
        )

        if not ok:

            self.send_json(
                400,
                {
                    "error": message
                }
            )

            return

        conn = get_db()

        conn.execute(
            """
            UPDATE pending_registrations
            SET email_verified = 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (registration_id,)
        )

        conn.commit()
        conn.close()

        self.send_json(
            200,
            {
                "success": True,
                "email_verified": True,
                "next_step": "phone"
            }
        )


    def verify_pending_phone(self, data):

        registration_id = data.get("registration_id")

        code = str(
            data.get("code", "")
        ).strip()

        phone_number = str(
            data.get("phone_number", "")
        ).strip()

        if not registration_id or not code or not phone_number:

            self.send_json(
                400,
                {
                    "error": (
                        "Registration ID, phone number and "
                        "verification code are required."
                    )
                }
            )

            return

        try:
            registration_id = int(registration_id)
        except (TypeError, ValueError):

            self.send_json(
                400,
                {
                    "error": "Invalid registration ID."
                }
            )

            return

        conn = get_db()

        registration = conn.execute(
            """
            SELECT
                id,
                email_verified,
                phone_number,
                phone_verified
            FROM pending_registrations
            WHERE id = ?
            """,
            (registration_id,)
        ).fetchone()

        conn.close()

        if not registration:

            self.send_json(
                404,
                {
                    "error": "Registration could not be found."
                }
            )

            return

        if not registration["email_verified"]:

            self.send_json(
                403,
                {
                    "error": "Email verification is required first."
                }
            )

            return

        if registration["phone_number"] != phone_number:

            self.send_json(
                400,
                {
                    "error": "Phone number does not match registration."
                }
            )

            return

        if registration["phone_verified"]:

            self.send_json(
                200,
                {
                    "success": True,
                    "phone_verified": True,
                    "next_step": "password"
                }
            )

            return

        ok, message = self.verify_pending_code(
            registration_id,
            "phone",
            code
        )

        if not ok:

            self.send_json(
                400,
                {
                    "error": message
                }
            )

            return

        conn = get_db()

        conn.execute(
            """
            UPDATE pending_registrations
            SET phone_verified = 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (registration_id,)
        )

        conn.commit()
        conn.close()

        self.send_json(
            200,
            {
                "success": True,
                "phone_verified": True,
                "next_step": "password"
            }
        )


    def verify_pending_code(
        self,
        registration_id,
        channel,
        code
    ):

        code = str(code).strip()

        if not code.isdigit() or len(code) != 6:

            return False, "Invalid verification code."

        code_hash = hashlib.sha256(
            code.encode("utf-8")
        ).hexdigest()

        conn = get_db()

        verification = conn.execute(
            """
            SELECT
                id,
                code_hash,
                expires_at,
                attempts,
                used
            FROM pending_verification_codes
            WHERE registration_id = ?
              AND channel = ?
              AND used = 0
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                registration_id,
                channel
            )
        ).fetchone()

        if not verification:

            conn.close()

            return False, "Verification code not found or already used."

        if verification["attempts"] >= 5:

            conn.execute(
                """
                UPDATE pending_verification_codes
                SET used = 1
                WHERE id = ?
                """,
                (verification["id"],)
            )

            conn.commit()
            conn.close()

            return False, "Too many verification attempts."

        try:
            expires_at = datetime.fromisoformat(
                verification["expires_at"]
            )

            if utc_now() > expires_at:

                conn.execute(
                    """
                    UPDATE pending_verification_codes
                    SET used = 1
                    WHERE id = ?
                    """,
                    (verification["id"],)
                )

                conn.commit()
                conn.close()

                return False, "Verification code has expired."

        except ValueError:

            conn.close()

            return False, "Invalid verification code."

        new_attempts = verification["attempts"] + 1

        if not secrets.compare_digest(
            verification["code_hash"],
            code_hash
        ):

            conn.execute(
                """
                UPDATE pending_verification_codes
                SET attempts = ?
                WHERE id = ?
                """,
                (
                    new_attempts,
                    verification["id"]
                )
            )

            if new_attempts >= 5:

                conn.execute(
                    """
                    UPDATE pending_verification_codes
                    SET used = 1
                    WHERE id = ?
                    """,
                    (verification["id"],)
                )

            conn.commit()
            conn.close()

            remaining = 5 - new_attempts

            if remaining <= 0:
                return False, "Too many verification attempts."

            return (
                False,
                f"Invalid verification code. "
                f"{remaining} attempts remaining."
            )

        conn.execute(
            """
            UPDATE pending_verification_codes
            SET used = 1,
                attempts = ?
            WHERE id = ?
            """,
            (
                new_attempts,
                verification["id"]
            )
        )

        conn.commit()
        conn.close()

        return True, "Verification successful."


    def complete_registration(self, data):

        registration_id = data.get("registration_id")

        password = str(
            data.get("password", "")
        )

        confirm_password = str(
            data.get("confirm_password", "")
        )

        if not registration_id or not password or not confirm_password:

            self.send_json(
                400,
                {
                    "error": (
                        "Registration ID, password and "
                        "password confirmation are required."
                    )
                }
            )

            return

        if password != confirm_password:

            self.send_json(
                400,
                {
                    "error": "Passwords do not match."
                }
            )

            return

        if len(password) < 8:

            self.send_json(
                400,
                {
                    "error": "Password must be at least 8 characters."
                }
            )

            return

        try:
            registration_id = int(registration_id)
        except (TypeError, ValueError):

            self.send_json(
                400,
                {
                    "error": "Invalid registration ID."
                }
            )

            return

        conn = get_db()

        registration = conn.execute(
            """
            SELECT
                id,
                full_name,
                email,
                phone_number,
                country,
                region,
                city,
                physical_address,
                identity_hash,
                email_verified,
                phone_verified
            FROM pending_registrations
            WHERE id = ?
            """,
            (registration_id,)
        ).fetchone()

        if not registration:

            conn.close()

            self.send_json(
                404,
                {
                    "error": "Registration could not be found."
                }
            )

            return

        if not registration["email_verified"]:

            conn.close()

            self.send_json(
                403,
                {
                    "error": "Email verification is required."
                }
            )

            return

        if not registration["phone_verified"]:

            conn.close()

            self.send_json(
                403,
                {
                    "error": "Phone verification is required."
                }
            )

            return

        existing_email = conn.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (registration["email"],)
        ).fetchone()

        if existing_email:

            conn.close()

            self.send_json(
                409,
                {
                    "error": (
                        "An account with this email already exists."
                    )
                }
            )

            return

        existing_identity = conn.execute(
            """
            SELECT id
            FROM users
            WHERE identity_hash = ?
            """,
            (registration["identity_hash"],)
        ).fetchone()

        if existing_identity:

            conn.close()

            self.send_json(
                409,
                {
                    "error": (
                        "An account is already registered "
                        "with this identity."
                    )
                }
            )

            return

        existing_phone = conn.execute(
            """
            SELECT id
            FROM users
            WHERE phone_number = ?
            """,
            (registration["phone_number"],)
        ).fetchone()

        if existing_phone:

            conn.close()

            self.send_json(
                409,
                {
                    "error": (
                        "An account with this phone number "
                        "already exists."
                    )
                }
            )

            return

        password_hash = hash_password(password)

        try:

            cursor = conn.execute(
                """
                INSERT INTO users (
                    full_name,
                    email,
                    password_hash,
                    role,
                    email_verified,
                    phone_number,
                    phone_verified,
                    country,
                    region,
                    city,
                    identity_hash,
                    updated_at
                )
                VALUES (?, ?, ?, 'user', 1, ?, 1, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    registration["full_name"],
                    registration["email"],
                    password_hash,
                    registration["phone_number"],
                    registration["country"],
                    registration["region"],
                    registration["city"],
                    registration["identity_hash"]
                )
            )

            user_id = cursor.lastrowid

            conn.execute(
                """
                DELETE FROM pending_verification_codes
                WHERE registration_id = ?
                """,
                (registration_id,)
            )

            conn.execute(
                """
                DELETE FROM pending_registrations
                WHERE id = ?
                """,
                (registration_id,)
            )

            conn.commit()
            conn.close()

        except sqlite3.IntegrityError:

            conn.rollback()
            conn.close()

            self.send_json(
                409,
                {
                    "error": (
                        "Registration could not be completed. "
                        "The account information may already exist."
                    )
                }
            )

            return

        self.send_json(
            201,
            {
                "success": True,
                "message": "Welcome to GODO AI.",
                "user_id": user_id,
                "next_step": "welcome"
            }
        )


    def register(self, data):

        full_name = str(
            data.get("full_name", "")
        ).strip()

        email = str(
            data.get("email", "")
        ).strip().lower()

        phone_number = str(
            data.get("phone_number", "")
        ).strip()

        country = str(
            data.get("country", "")
        ).strip()

        region = str(
            data.get("region", "")
        ).strip()

        city = str(
            data.get("city", "")
        ).strip()

        identity_number = str(
            data.get("identity_number", "")
        ).strip()

        password = str(
            data.get("password", "")
        )


        if not all([
            full_name,
            email,
            phone_number,
            country,
            region,
            city,
            identity_number,
            password
        ]):

            self.send_json(
                400,
                {
                    "error": "All registration fields are required."
                }
            )

            return


        if len(password) < 8:

            self.send_json(
                400,
                {
                    "error": "Password must be at least 8 characters."
                }
            )

            return


        try:

            identity_hash = hash_identity(
                identity_number
            )

        except RuntimeError as error:

            print("Registration security error:", error)

            self.send_json(
                500,
                {
                    "error": "Registration security is not configured."
                }
            )

            return


        conn = get_db()


        existing_email = conn.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()


        if existing_email:

            conn.close()

            self.send_json(
                409,
                {
                    "error": "An account with this email already exists."
                }
            )

            return


        existing_identity = conn.execute(
            """
            SELECT id
            FROM users
            WHERE identity_hash = ?
            """,
            (identity_hash,)
        ).fetchone()


        if existing_identity:

            conn.close()

            self.send_json(
                409,
                {
                    "error": (
                        "An account is already registered "
                        "with this identity."
                    )
                }
            )

            return


        existing_phone = conn.execute(
            """
            SELECT id
            FROM users
            WHERE phone_number = ?
            """,
            (phone_number,)
        ).fetchone()


        if existing_phone:

            conn.close()

            self.send_json(
                409,
                {
                    "error": (
                        "An account with this phone number "
                        "already exists."
                    )
                }
            )

            return


        password_hash = hash_password(
            password
        )


        try:

            cursor = conn.execute(
                """
                INSERT INTO users (
                    full_name,
                    email,
                    password_hash,
                    role,
                    email_verified,
                    phone_number,
                    phone_verified,
                    country,
                    region,
                    city,
                    identity_hash,
                    updated_at
                )
                VALUES (?, ?, ?, 'user', 0, ?, 0, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    full_name,
                    email,
                    password_hash,
                    phone_number,
                    country,
                    region,
                    city,
                    identity_hash
                )
            )

            conn.commit()

            user_id = cursor.lastrowid

            conn.close()


        except sqlite3.IntegrityError:

            conn.close()

            self.send_json(
                409,
                {
                    "error": (
                        "Registration could not be completed. "
                        "The account information may already exist."
                    )
                }
            )

            return


        # Create one-time verification codes.
        # Only hashed codes are stored in the database.
        email_otp = self.create_verification_code(
            user_id,
            "registration",
            "email",
            email
        )

        phone_otp = self.create_verification_code(
            user_id,
            "registration",
            "phone",
            phone_number
        )


        # Send the email verification code.
        # The raw OTP is sent only to the user's email.
        # Only its hash is stored in the database.
        try:

            send_verification_email(
                email,
                email_otp
            )

        except Exception as error:

            print(
                "Email verification delivery error:",
                error
            )

            self.send_json(
                503,
                {
                    "success": False,
                    "error": (
                        "Account created, but the verification "
                        "email could not be sent. Please try again."
                    )
                }
            )

            return


        # Development-only logging.
        # Never expose these codes through the production API response.
        print(
            f"🔐 Registration verification generated for user {user_id}"
        )


        self.send_json(
            201,
            {
                "success": True,
                "message": (
                    "GODO AI account created. "
                    "Email and phone verification required."
                ),
                "user_id": user_id,
                "verification": {
                    "email_verified": False,
                    "phone_verified": False
                }
            }
        )


    def login(self, data):

        email = str(
            data.get("email", "")
        ).strip().lower()

        password = str(
            data.get("password", "")
        )


        if not email or not password:

            self.send_json(
                400,
                {
                    "error": "Email and password are required."
                }
            )

            return


        conn = get_db()

        user = conn.execute(
            """
            SELECT id, full_name, email, password_hash, role
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        conn.close()


        if not user:

            self.send_json(
                401,
                {
                    "error": "Invalid email or password."
                }
            )

            return


        if not verify_password(
            password,
            user["password_hash"]
        ):

            self.send_json(
                401,
                {
                    "error": "Invalid email or password."
                }
            )

            return


        session_token = secrets.token_urlsafe(32)

        conn = get_db()

        conn.execute(
            """
            INSERT INTO sessions (user_id, token)
            VALUES (?, ?)
            """,
            (user["id"], session_token)
        )

        conn.commit()
        conn.close()


        self.send_json(
            200,
            {
                "success": True,
                "message": "Login successful.",
                "session_token": session_token,
                "user": {
                    "id": user["id"],
                    "full_name": user["full_name"],
                    "email": user["email"],
                    "role": user["role"]
                }
            }
        )


if __name__ == "__main__":

    init_db()

    print(
        f"🔐 GODO AI Auth Backend running on http://{HOST}:{PORT}"
    )

    server = HTTPServer(
        (HOST, PORT),
        AuthHandler
    )

    server.serve_forever()
