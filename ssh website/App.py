import asyncio
import hashlib
import tornado.web
import json
import os
import Backend

# Caricamento utenti da file JSON
with open("users.json") as f:
    users = json.load(f)


# INDEX
# -------------------------------------------------------------------------------------------------------------------------------------------------
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        user = self.get_secure_cookie("user")
        if user:
            username = user.decode("utf-8")
            self.render("index.html", log=True, username=username,
                        message=f"Benvenuto {username}, sei loggato! INSERISCI IL FILE .GPX!", errore="")
        else:
            self.render("index.html", log=False, username="",
                        message="Per inserire il file devi essere loggato!", errore="")



# REGISTER
# ----------------------------------------------------------------------------------------------------------------------------------------------
class RegisterHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("register.html", message="Registrati", errore="", log=False)

    def post(self):
        prestanza = self.get_body_argument("prestanza", None)
        username = self.get_body_argument("username")

        if prestanza is None:
            # Step 1: Registrazione username e password
            password = self.get_body_argument("password")

            if username in users:
                self.write(json.dumps({"success": False, "message": "Username già in uso"}))
                return

            # Hash della password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            users[username] = {"password": hashed_password, "prestanza": None}

            # Salva i dati su file
            with open("users.json", "w") as d:
                json.dump(users, d)

            self.write(json.dumps({"success": True}))
        else:
            # Step 2: Aggiorna livello di prestanza
            if username not in users:
                self.write(json.dumps({"success": False, "message": "Utente non trovato"}))
                return

            users[username]["prestanza"] = prestanza

            # Salva i dati su file
            with open("users.json", "w") as d:
                json.dump(users, d)

            self.write(json.dumps({"success": True, "redirect": "/login"}))


# LOGOUT ------------------------------------------------------------------------------------------------------------------------------------------------------------
class LogoutHandler(tornado.web.RequestHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect("/")


# LOGIN -------------------------------------------------------------------------------------------------------------------------------------------------------------
class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("login.html", message="Inserisci le tue credenziali", log=False, errore="")

    def post(self):
        username = self.get_body_argument("username")
        password = self.get_body_argument("password")

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        if username in users and users[username]["password"] == hashed_password:
            self.set_secure_cookie("user", username, secure=True, httponly=True)
            self.render("index.html", log=True, username=username,
                        message=f"Benvenuto {username}, sei loggato! INSERISCI IL FILE .GPX!", errore="")
        else:
            self.render("login.html", message="Username o password errata. Riprova.", log=False, errore="")



# CARICA FILE ----------------------------------------------------------------------------------------------------------------------------------------------------------------
class CaricaFile(tornado.web.RequestHandler):

    def post(self):
        user = self.get_secure_cookie("user")


        if 'file' not in self.request.files:
            self.render("index.html", message=f"Benvenuto, sei loggato! INSERISCI IL FILE .GPX!", log=True,
                        errore="Nessun file caricato! Riprova.", username=user.decode())
            return

        uploaded_file = self.request.files['file'][0]
        filename = uploaded_file['filename']

        # Definisci la directory di destinazione per i file
        upload_dir = os.path.join(os.getcwd(), "uploads")
        os.makedirs(upload_dir, exist_ok=True)  # Crea la cartella se non esiste

        # Crea il path completo del file
        full_path = os.path.join(upload_dir, filename)

        # Salva il file sul server
        with open(full_path, 'wb') as f:
            f.write(uploaded_file['body'])

        # Se vuoi il percorso assoluto del file, puoi usare:
        absolute_path = os.path.abspath(full_path)

        # Ora puoi usare `absolute_path` per passarla ad altre funzioni o per ulteriori elaborazioni
        durata = Backend.main(absolute_path, users[user.decode()]["prestanza"])

        punti_lista = Backend.punti(absolute_path)  # Ottieni la lista dai punti del file GPX

        if punti_lista is not None:
            punti_json = json.dumps(punti_lista)
            print(type(punti_json))
        else:
            punti_json = '{}'

        self.render("Durata.html", durata=durata, log=True, username=user.decode(), punti=punti_json)





def make_app():
    settings = {
        "template_path": "templates",
        "static_path": "static/",
        "cookie_secret": os.getenv("COOKIE_SECRET", "default_secret"),
        "debug": True
    }

    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/login", LoginHandler),
        (r"/register", RegisterHandler),
        (r"/logout", LogoutHandler),
        (r"/upload", CaricaFile),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "static"}),
    ], **settings)


async def main():
    port = 80
    app = make_app()
    app.listen(port)
    print(f"Server started at {port}: http://localhost:{port}/")
    try:
        await asyncio.Event().wait()
    finally:
        users.clear()
        print("Cookies cancellati e utenti sloggati.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
