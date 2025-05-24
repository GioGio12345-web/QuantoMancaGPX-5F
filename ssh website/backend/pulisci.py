import os
import requests

# Configurazione
folder_path = "/home/studente/PythonProject/PythonProject1/Tracce gpx"  # Modifica con il tuo percorso
upload_url = "https://www.omnib.it/trackPaint/index.php"

# Creazione della cartella per i file puliti
clean_folder = os.path.join(folder_path, "cleaned")
os.makedirs(clean_folder, exist_ok=True)

# Scansione ricorsiva delle sottocartelle
for root, _, files in os.walk(folder_path):
    for filename in files:
        if filename.endswith(".gpx"):
            file_path = os.path.join(root, filename)
            with open(file_path, 'rb') as f:
                files = {'gpxfile': f}
                response = requests.post(upload_url, files=files)

            if response.status_code == 200:
                clean_file_path = os.path.join(clean_folder, filename)
                with open(clean_file_path, 'wb') as out_file:
                    out_file.write(response.content)
                print(f"File pulito salvato: {clean_file_path}")
            else:
                print(f"Errore nell'elaborazione di {filename}: {response.status_code}")

print("Processo completato!")

