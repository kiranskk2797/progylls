"""Run with python progylls_server.py, then open http://localhost:8765."""
import hashlib
import hmac
import json
import os
import secrets
import smtplib
import sqlite3
import ssl
import time
from email.message import EmailMessage
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get("PROGYLLS_DATA", ROOT / ".progylls-data"))
PORT = int(os.environ.get("PROGYLLS_PORT", "8765"))


def database():
    return sqlite3.connect(DATA / "accounts.sqlite3")


def digest(password, salt):
    return hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)


def send_reset(email, token):
    message = EmailMessage()
    message["From"] = os.environ["PROGYLLS_MAIL_FROM"]
    message["To"] = email
    message["Subject"] = "Reset your ProGylls password"
    base = os.environ.get("PROGYLLS_PUBLIC_URL", f"http://localhost:{PORT}").rstrip("/")
    message.set_content(f"Open this link to choose a new ProGylls password within 15 minutes.\n\n"
                        f"{base}/recovery#reset/{token}\n\nIf you did not request this, you can ignore this email.")
    with smtplib.SMTP_SSL(os.environ["PROGYLLS_SMTP_HOST"], int(os.getenv("PROGYLLS_SMTP_PORT", "465")),
                          context=ssl.create_default_context(), timeout=10) as smtp:
        if os.getenv("PROGYLLS_SMTP_USER"):
            smtp.login(os.environ["PROGYLLS_SMTP_USER"], os.environ["PROGYLLS_SMTP_PASSWORD"])
        smtp.send_message(message)


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body=b"", kind="text/plain", **headers):
        self.send_response(status)
        for name, value in {"Content-Type": kind, "Content-Length": str(len(body)),
                            "Cache-Control": "no-store", **headers}.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def token(self):
        cookies = SimpleCookie(self.headers.get("Cookie", ""))
        token = cookies.get("pg_session")
        return hashlib.sha256((token.value if token else "").encode()).hexdigest()

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/recovery":
            return self.reply(200, (ROOT / "practice-preview.html").read_bytes(), "text/html; charset=utf-8")
        if path not in ("/", "/app"):
            return self.reply(404)
        with database() as db:
            account = db.execute("""SELECT sessions.user_id,
                                    learner_stages.user_id IS NOT NULL AND stage IS NULL
                                    FROM sessions LEFT JOIN learner_stages USING(user_id)
                                    WHERE token=? AND expires>?""",
                                 (self.token(), time.time())).fetchone()
        if path == "/app" and not account:
            return self.reply(303, Location="/")
        if path == "/" and account:
            return self.reply(303, Location="/app")
        if account:
            html = (ROOT / "ProGylls.html").read_text(encoding="utf-8")
            html = html.replace("const KEY='progylls-proto-v2';",
                                f"const KEY='progylls-account-{account[0]}';")
            if account[1]:
                html = html.replace("let needsStage=false;", "let needsStage=true;")
            html = html.replace('<button class="avatar"', '<form method="post" action="/logout"><button class="link" type="submit">Log out</button></form><button class="avatar"')
        else:
            html = (ROOT / "practice-preview.html").read_text(encoding="utf-8")
        self.reply(200, html.encode(), "text/html; charset=utf-8")

    def do_POST(self):
        origin = self.headers.get("Origin")
        if origin and origin != "http://" + self.headers.get("Host", ""):
            return self.reply(403)
        if self.path == "/logout":
            with database() as db:
                db.execute("DELETE FROM sessions WHERE token=?", (self.token(),))
            return self.reply(303, Location="/", **{"Set-Cookie": "pg_session=; HttpOnly; Path=/; SameSite=Strict; Max-Age=0"})
        if self.path not in ("/signup", "/login", "/stage", "/forgot", "/reset"):
            return self.reply(404)
        try:
            size = int(self.headers.get("Content-Length", 0))
            if not 0 < size <= 4096 or self.headers.get_content_type() != "application/json":
                return self.reply(400)
            fields = json.loads(self.rfile.read(size))
            if self.path == "/forgot":
                return self.request_reset(fields["email"].strip().lower())
            if self.path == "/reset":
                return self.reset_password(fields["token"], fields["password"])
            if self.path == "/stage":
                stage = fields.get("stage")
                if stage not in ("new", "job-seeking", "transitioning"):
                    return self.reply(400, b"Choose one of the three stages.")
                with database() as db:
                    session = db.execute("SELECT user_id FROM sessions WHERE token=? AND expires>?",
                                         (self.token(), time.time())).fetchone()
                    if not session:
                        return self.reply(401)
                    db.execute("UPDATE learner_stages SET stage=? WHERE user_id=? AND stage IS NULL",
                               (stage, session[0]))
                return self.reply(200, b"OK")
            email = fields["email"].strip().lower()
            password = fields["password"]
            if not isinstance(password, str) or len(password) > 256 or len(email) > 254:
                raise ValueError
        except (TypeError, AttributeError, KeyError, ValueError):
            return self.reply(400, b"Check your email and password.")
        with database() as db:
            if self.path == "/signup":
                if email.count("@") != 1 or not all(email.split("@")) or len(password) < 10:
                    return self.reply(400, b"Enter an email and a password of at least 10 characters.")
                salt = secrets.token_bytes(16)
                try:
                    user_id = db.execute("INSERT INTO users(email,salt,password) VALUES (?,?,?)",
                                         (email, salt, digest(password, salt))).lastrowid
                    db.execute("INSERT INTO learner_stages(user_id) VALUES (?)", (user_id,))
                except sqlite3.IntegrityError:
                    return self.reply(409, b"This email already has an account. Choose Log in below.")
            else:
                row = db.execute("SELECT id,salt,password FROM users WHERE email=?", (email,)).fetchone()
                computed = digest(password, row[1] if row else bytes(16))
                if not row or not hmac.compare_digest(computed, row[2]):
                    return self.reply(401, b"Check your email and password and try again.")
                user_id = row[0]
            raw = secrets.token_urlsafe(32)
            db.execute("DELETE FROM sessions WHERE expires<=?", (time.time(),))
            db.execute("INSERT INTO sessions VALUES (?,?,?)",
                       (hashlib.sha256(raw.encode()).hexdigest(), user_id, time.time() + 604800))
        self.reply(200, b"OK", **{"Set-Cookie": f"pg_session={raw}; Path=/; HttpOnly; SameSite=Strict; Max-Age=604800"})

    def request_reset(self, email):
        if len(email) > 254 or email.count("@") != 1 or any(c.isspace() for c in email):
            return self.reply(400, b"Enter a valid email address.")
        if not os.getenv("PROGYLLS_SMTP_HOST") or not os.getenv("PROGYLLS_MAIL_FROM"):
            return self.reply(503, b"Reset emails are unavailable until the app owner connects email delivery.")
        now = time.time()
        raw = secrets.token_urlsafe(32)
        hashed = hashlib.sha256(raw.encode()).hexdigest()
        with database() as db:
            db.execute("BEGIN IMMEDIATE")
            user = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
            if not user:
                return self.reply(200)
            recent = db.execute("SELECT 1 FROM resets WHERE user_id=? AND expires>?",
                                (user[0], now + 840)).fetchone()
            if recent:
                return self.reply(200)
            db.execute("INSERT OR REPLACE INTO resets VALUES (?,?,?)", (user[0], hashed, now + 900))
        try:
            send_reset(email, raw)
        except (OSError, smtplib.SMTPException, KeyError, ValueError):
            with database() as db:
                db.execute("DELETE FROM resets WHERE token=?", (hashed,))
            return self.reply(503, b"Email delivery is temporarily unavailable. Please try again later.")
        return self.reply(200)

    def reset_password(self, token, password):
        if not isinstance(password, str) or not 10 <= len(password) <= 256:
            return self.reply(400, b"Use a password of 10 to 256 characters.")
        if not isinstance(token, str) or len(token) != 43:
            return self.reply(400, b"This link is invalid or expired. Request a new reset link.")
        hashed = hashlib.sha256(token.encode()).hexdigest()
        with database() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT user_id FROM resets WHERE token=? AND expires>?",
                             (hashed, time.time())).fetchone()
            if not row:
                return self.reply(400, b"This link is invalid or expired. Request a new reset link.")
            salt = secrets.token_bytes(16)
            db.execute("UPDATE users SET salt=?, password=? WHERE id=?", (salt, digest(password, salt), row[0]))
            db.execute("DELETE FROM resets WHERE user_id=?", row)
            db.execute("DELETE FROM sessions WHERE user_id=?", row)
        self.reply(200)


if __name__ == "__main__":
    DATA.mkdir(parents=True, exist_ok=True)
    with database() as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT UNIQUE,
                                              salt BLOB, password BLOB);
            CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user_id INTEGER, expires REAL);
            CREATE TABLE IF NOT EXISTS learner_stages(user_id INTEGER PRIMARY KEY, stage TEXT);
            CREATE TABLE IF NOT EXISTS resets(user_id INTEGER PRIMARY KEY, token TEXT UNIQUE, expires REAL);
        """)
    print(f"Open http://localhost:{PORT}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
