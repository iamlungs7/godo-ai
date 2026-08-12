import json
import sqlite3
import hashlib
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 8000

DB_PATH = "backend/database/godo_ai.db"


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
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
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
            "http://127.0.0.1:8080"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
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
            "http://127.0.0.1:8080"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

        self.end_headers()

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
            SELECT id, full_name, email, password_hash
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


        self.send_json(
            200,
            {
                "success": True,
                "message": "Login successful.",
                "session_token": session_token,
                "user": {
                    "id": user["id"],
                    "full_name": user["full_name"],
                    "email": user["email"]
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
