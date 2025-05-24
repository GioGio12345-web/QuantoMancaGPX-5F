
import json
import gpxpy
import gpxpy.gpx
import charset_normalizer
from gpxpy.geo import distance
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

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
        if d != 0:  # Controllo per evitare la divisione per zero
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


with open("/home/studente/PythonProject/PythonProject1/dataset.json", "r") as f:
    data = json.load(f)

data_df = pd.DataFrame(data)
data_df['avg_speed'] = data_df['distance'] / (data_df['time'] * 60)

X = data_df[['distance', 'slope', 'ascent', 'descent', 'avg_speed']]
y = data_df['time']

# Machine Learning
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=6, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print(f"Mean Squared Error: {mse}")

# Predizione su un nuovo file
file_path_trova = "/home/studente/PythonProject/PythonProject1/a.gpx"
gpx_t = uniforma_file_gpx(file_path_trova)
if gpx_t:
    vt = []
    for track in gpx_t.tracks:
        for segment in track.segments:
            for point in segment.points:
                vt.append((point.latitude, point.longitude, point.elevation))

    new_data = pd.DataFrame({
        'distance': [trova_dist(vt)],
        'slope': [trova_pend(vt)],
        'ascent': [calcola_dislivello(vt)[0]],
        'descent': [calcola_dislivello(vt)[1]],
        'avg_speed': [trova_dist(vt) / (28 * 60)]
    })

    new_data_scaled = scaler.transform(new_data)
    predicted_time = model.predict(new_data_scaled)[0]

    hours = int(predicted_time // 60)
    minutes = int(predicted_time % 60)
    seconds = int((predicted_time * 60) % 60)
    print(f"Tempo previsto: {hours}h {minutes}m {seconds}s")
print('errore')
