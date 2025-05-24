import os
import gpxpy
import gpxpy.gpx
import charset_normalizer
from gpxpy.geo import distance
import json

# Funzione per calcolare la distanza totale
def trova_dist(v):
    if len(v) < 2:
        return 0
    d = 0
    for i in range(len(v) - 1):
        d += distance(v[i][0], v[i][1], v[i][2], v[i + 1][0], v[i + 1][1], v[i + 1][2])
    return d

# Funzione per calcolare la pendenza media
def trova_pend(v):
    if len(v) < 2:
        return 0
    total_pend = 0
    count = 0
    for i in range(len(v) - 1):
        d = distance(v[i][0], v[i][1], 0, v[i + 1][0], v[i + 1][1], 0)
        h = v[i + 1][2] - v[i][2]
        if d != 0:
            total_pend += (h / d * 100)
            count += 1
    return total_pend / count if count > 0 else 0

# Funzione per calcolare il tempo totale
def trova_tempo(gpx):
    total_duration = 0
    for track in gpx.tracks:
        for segment in track.segments:
            if len(segment.points) > 1:
                start_time = segment.points[0].time
                end_time = segment.points[-1].time
                if start_time and end_time:
                    total_duration += (end_time - start_time).total_seconds()
    return total_duration

# Funzione per calcolare il dislivello totale
def calcola_dislivello(v):
    if len(v) < 2:
        return 0, 0
    total_ascent = 0
    total_descent = 0
    for i in range(len(v) - 1):
        diff = v[i + 1][2] - v[i][2]
        if diff > 0:
            total_ascent += diff
        elif diff < 0:
            total_descent += abs(diff)
    return total_ascent, total_descent

# Funzione per uniformare i file GPX
def uniforma_file_gpx(file_path):
    try:
        with open(file_path, "rb") as f:
            raw_data = f.read()
            detected = charset_normalizer.detect(raw_data)
            encoding = detected["encoding"] if detected["encoding"] else "utf-8"

        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            gpx = gpxpy.parse(f)
        return gpx
    except Exception as e:
        print(f"Errore nella formattazione di {file_path}: {e}")
        return None

# Percorso ai file GPX
cartella = "/home/studente/PythonProject/PythonProject1/Tracce gpx"
distanze, pendenze, tempi, dislivello_salita, dislivello_discesa = [], [], [], [], []

for root, dirs, files in os.walk(cartella):
    for file in files:
        file_path = os.path.join(root, file)

        gpx = uniforma_file_gpx(file_path)
        if not gpx:
            continue

        v = []
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    v.append((point.latitude, point.longitude, point.elevation, point.time))

        if len(v) < 2:
            print(f"File GPX '{file_path}' ha troppi pochi punti.")
            continue

        if trova_tempo(gpx) != 0:
            distanze.append(trova_dist(v))
            pendenze.append(trova_pend(v))
            tempi.append(trova_tempo(gpx) / 60)
            ascent, descent = calcola_dislivello(v)
            dislivello_salita.append(ascent)
            dislivello_discesa.append(descent)

if not distanze:
    print("Errore: il dataset è vuoto. Verifica la lettura dei file GPX.")
else:
    data = {
        'distance': distanze,
        'slope': pendenze,
        'time': tempi,
        'ascent': dislivello_salita,
        'descent': dislivello_discesa
        #'prestanza' : livello_prestanza
    }

    with open("/home/studente/PythonProject/PythonProject1/dataset.json", "w") as f:
        json.dump(data, f)
    print("File JSON creato con successo!")
