import json
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

HOST = "0.0.0.0"
PORT = int(__import__("os").environ.get("PORT", "8000"))

DB_PATH = __import__("os").environ.get("GODO_AI_DB_PATH", "backend/database/godo_ai.db")


def get_db():
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

    conn.commit()
    conn.close()


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


    def register(self, data):

        full_name = str(
            data.get("full_name", "")
        ).strip()

        email = str(
            data.get("email", "")
        ).strip().lower()

        password = str(
            data.get("password", "")
        )


        if not full_name or not email or not password:

            self.send_json(
                400,
                {
                    "error": "All fields are required."
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


        password_hash = hash_password(
            password
        )


        try:

            conn = get_db()

            conn.execute(
                """
                INSERT INTO users
                (full_name, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (
                    full_name,
                    email,
                    password_hash
                )
            )

            conn.commit()

            user_id = conn.execute(
                "SELECT last_insert_rowid()"
            ).fetchone()[0]

            conn.close()


            self.send_json(
                201,
                {
                    "success": True,
                    "message": "GODO AI account created.",
                    "user_id": user_id
                }
            )


        except sqlite3.IntegrityError:

            self.send_json(
                409,
                {
                    "error": "An account with this email already exists."
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
