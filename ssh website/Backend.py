import json
import gpxpy
import gpxpy.gpx
import charset_normalizer
from gpxpy.geo import distance
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from xgboost import XGBRegressor



# --- Funzioni di estrazione del percorso ---
def trova_dist(points):
    """Calcola la distanza totale (in metri) lungo una lista di punti."""
    if len(points) < 2:
        return 0
    d = 0
    for i in range(len(points) - 1):
        d += distance(points[i][0], points[i][1], points[i][2],
                      points[i + 1][0], points[i + 1][1], points[i + 1][2])
    return d


def trova_pend(points):
    """Calcola la pendenza media percentuale lungo la sequenza di punti."""
    if len(points) < 2:
        return 0
    total_pend = 0
    count = 0
    for i in range(len(points) - 1):
        # Considero solo la distanza orizzontale
        d = distance(points[i][0], points[i][1], 0,
                     points[i + 1][0], points[i + 1][1], 0)
        h = points[i + 1][2] - points[i][2]
        if d != 0:
            total_pend += (h / d * 100)
            count += 1
    return total_pend / count if count > 0 else 0


def calcola_dislivello(points):
    """Calcola il dislivello positivo e negativo (in metri) lungo il percorso."""
    if len(points) < 2:
        return 0, 0
    total_ascent = 0
    total_descent = 0
    for i in range(len(points) - 1):
        diff = points[i + 1][2] - points[i][2]
        if diff > 0:
            total_ascent += diff
        elif diff < 0:
            total_descent += abs(diff)
    return total_ascent, total_descent


def uniforma_file_gpx(file_path):
    """Legge e parsifica un file GPX gestendo eventuali problemi di encoding."""
    try:
        with open(file_path, "rb") as f:
            raw_data = f.read()
            detected = charset_normalizer.detect(raw_data)
            encoding = detected["encoding"] if detected["encoding"] else "utf-8"
        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            gpx = gpxpy.parse(f)
        return gpx
    except Exception as e:
        print(f"Errore nella lettura di {file_path}: {e}")
        return None


def format_time(minutes):
    """Converte i minuti (float) in ore, minuti e secondi."""
    total_secs = int(round(minutes * 60))
    hrs = total_secs // 3600
    rem = total_secs % 3600
    mins = rem // 60
    secs = rem % 60
    if hrs == 0 :
        return f"{mins} minuti e {secs} secondi"
    else:
        return f"{hrs} ore, {mins} minuti e {secs} secondi"



# --- Training del modello ---

# Carico il dataset. Assicurati che "dataset.json" contenga le seguenti chiavi:
# - distance (in metri)
# - slope (pendenza media percentuale)
# - ascent (dislivello positivo in metri)
# - descent (dislivello negativo in metri)
# - time (tempo in minuti)



# --- Funzione che prende i punti dal file ---
def punti(file_path):
    gpx_data = uniforma_file_gpx(file_path)
    if not gpx_data:
        return None

    # Estrazione di tutti i punti dal file GPX
    points = []
    for track in gpx_data.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append((point.latitude, point.longitude, point.elevation))

    if len(points) < 2:
        print("Il percorso è troppo breve per l'analisi.")
        return None

    return points


# --- Funzione di predizione per un file GPX ---
def predict_hiking_time(model, scaler, default_speed, path, fitness_level="intermediate"):
    points=punti(path)
    total_distance = trova_dist(points)
    avg_slope = trova_pend(points)
    total_ascent, total_descent = calcola_dislivello(points)

    # Prepara le feature in un DataFrame per il modello:
    features = pd.DataFrame({
        'distance': [total_distance],
        'slope': [avg_slope],
        'ascent': [total_ascent],
        'descent': [total_descent],
        # Per avg_speed usiamo il valore medio del dataset
        'avg_speed': [default_speed]
    })

    # Prevede il tempo in minuti
    predicted_time = model.predict(scaler.transform(features))[0]

    # Fattore di aggiustamento in base al livello di preparazione fisica
    adjustment_factors = {
        "professional": 0.8,
        "advanced": 0.9,
        "intermediate": 1.0,
        "beginner": 1.1,
        "sedentary": 1.2
    }
    factor = adjustment_factors.get(fitness_level.lower(), 1.0)
    adjusted_time = predicted_time * factor

    return adjusted_time


# --- Utilizzo interattivo ---


def main(path, livello):
    with open("backend/dataset.json", "r") as f:
        data = json.load(f)

    data_df = pd.DataFrame(data)

    # Calcolo della feature avg_speed (in m/s) come da dataset:
    #   avg_speed = distance / (time * 60)
    data_df['avg_speed'] = data_df['distance'] / (data_df['time'] * 60)

    # Selezione delle feature e target
    X = data_df[['distance', 'slope', 'ascent', 'descent', 'avg_speed']]
    y = data_df['time']  # tempo in minuti

    # Normalizzazione degli input
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # Suddivido in training e test (questo serve solo a verificare la prestazione)
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    # Addestro il modello (XGBoost in questo caso)
    model = XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=20, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f"Mean Squared Error sul test: {mse:.2f}")

    # Per coerenza, calcoliamo il valore medio della feature avg_speed (in m/s) presente nel dataset.
    default_speed = data_df['avg_speed'].mean()


    # Chiedi all'utente il file GPX da analizzare (in questo esempio viene usato un file fisso)
    file_path = path

    #prendo il livello di prestanza fisica
    user_level = livello

    # Se l'input non corrisponde a una delle opzioni, usa 'intermediate' come default
    if user_level not in ("professionista", "avanzato", "intermedio", "principiante", "sedentario"):
        user_level = "intermedio"

    predicted_minutes = predict_hiking_time(model, scaler, default_speed, file_path, user_level)

    if predicted_minutes is not None:
        return format_time(predicted_minutes)
    return "Tempo calcolato non correttamente"




