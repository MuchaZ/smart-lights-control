import math
from datetime import datetime

room_id = data.get("room_id")
sample = data.get("sample")

if not room_id or not sample:
    logger.warning("Brak room_id lub sample w danych wejściowych")
    exit()

# Sprawdź format próbki - powinna być "brightness:lux"
if ":" not in sample:
    logger.warning(f"Nieprawidłowy format próbki: {sample}. Oczekiwany format: 'brightness:lux'")
    exit()

history_entity = f"input_text.brightness_lux_samples_{room_id}"

try:
    brightness_str, lux_str = sample.split(":", 1)
    brightness = float(brightness_str)
    lux = float(lux_str)
except (ValueError, AttributeError):
    logger.warning(f"Błąd parsowania próbki: {sample}")
    exit()

# Walidacja danych
if not (0 <= brightness <= 255):
    logger.warning(f"Nieprawidłowa jasność: {brightness} (zakres: 0-255)")
    exit()

if lux < 0 or lux > 10000:
    logger.warning(f"Nieprawidłowa wartość lux: {lux} (zakres: 0-10000)")
    exit()

# Pobierz historię próbek
history_state = hass.states.get(history_entity)
if history_state and history_state.state != "unknown" and history_state.state != "unavailable":
    history_samples = [s.strip() for s in history_state.state.split(";") if s.strip()]
else:
    history_samples = []

# Dodaj znacznik czasu do próbki dla lepszego debugowania
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
timestamped_sample = f"{sample}#{timestamp}"

# Dodaj nową próbkę i zachowaj ostatnie 50 (zwiększone z 20)
history_samples.append(timestamped_sample)
history_samples = history_samples[-50:]

# Zapisz historię
new_history = ";".join(history_samples)
hass.states.set(history_entity, new_history)

# Parsuj próbki do regresji (usuń znaczniki czasu)
brightness_vals = []
lux_vals = []

for sample_entry in history_samples:
    try:
        # Usuń znacznik czasu jeśli istnieje
        clean_sample = sample_entry.split("#")[0]
        if ":" not in clean_sample:
            continue
            
        b_str, l_str = clean_sample.split(":", 1)
        b = float(b_str)
        l = float(l_str)
        
        # Walidacja
        if 0 <= b <= 255 and 0 <= l <= 10000:
            brightness_vals.append(b)
            lux_vals.append(l)
    except:
        continue

n = len(brightness_vals)
if n < 5:
    logger.info(f"Za mało danych do regresji: {n}/5. Zbieranie próbek...")
    exit()

# Usuń duplikaty i outliery
def clean_data(x_vals, y_vals):
    # Usuń duplikaty
    pairs = list(set(zip(x_vals, y_vals)))
    if len(pairs) < len(x_vals):
        logger.info(f"Usunięto {len(x_vals) - len(pairs)} duplikatów")
    
    x_clean = [p[0] for p in pairs]
    y_clean = [p[1] for p in pairs]
    
    # Usuń outliery tylko gdy mamy dużo danych
    if len(x_clean) >= 10:
        x_mean = sum(x_clean) / len(x_clean)
        y_mean = sum(y_clean) / len(y_clean)
        x_std = math.sqrt(sum((x - x_mean) ** 2 for x in x_clean) / len(x_clean))
        y_std = math.sqrt(sum((y - y_mean) ** 2 for y in y_clean) / len(y_clean))
        
        filtered_pairs = []
        for x, y in pairs:
            if (abs(x - x_mean) < 2.5 * x_std and abs(y - y_mean) < 2.5 * y_std):
                filtered_pairs.append((x, y))
        
        if len(filtered_pairs) >= 5:  # Zachowaj przynajmniej 5 punktów
            outliers_removed = len(pairs) - len(filtered_pairs)
            if outliers_removed > 0:
                logger.info(f"Usunięto {outliers_removed} outlierów")
            return [p[0] for p in filtered_pairs], [p[1] for p in filtered_pairs]
    
    return x_clean, y_clean

brightness_vals, lux_vals = clean_data(brightness_vals, lux_vals)
n = len(brightness_vals)

if n < 3:
    logger.warning("Za mało danych po czyszczeniu")
    exit()

# Regresja liniowa: lux = a * brightness + b
x_vals = brightness_vals
y_vals = lux_vals

avg_x = sum(x_vals) / n
avg_y = sum(y_vals) / n

numerator = sum((x - avg_x) * (y - avg_y) for x, y in zip(x_vals, y_vals))
denominator = sum((x - avg_x) ** 2 for x in x_vals)

if denominator == 0:
    logger.warning("Wszystkie wartości jasności identyczne - brak regresji")
    exit()

a = numerator / denominator
b = avg_y - a * avg_x

# Oblicz R²
y_pred = [a * x + b for x in x_vals]
ss_res = sum((y_actual - y_pred) ** 2 for y_actual, y_pred in zip(y_vals, y_pred))
ss_tot = sum((y - avg_y) ** 2 for y in y_vals)
r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

logger.info(f"Nowa regresja {room_id}: a={a:.4f}, b={b:.1f}, R²={r_squared:.3f}, próbek={n}")

# Aktualizuj encje Home Assistant
a_entity = f"input_number.light_regression_a_{room_id}"
b_entity = f"input_number.light_regression_b_{room_id}"
quality_entity = f"input_number.regression_quality_{room_id}"

try:
    hass.services.call("input_number", "set_value", {
        "entity_id": a_entity,
        "value": round(a, 4)
    }, False)

    hass.services.call("input_number", "set_value", {
        "entity_id": b_entity,
        "value": round(b, 1)
    }, False)
    
    # Opcjonalnie zapisz jakość
    hass.services.call("input_number", "set_value", {
        "entity_id": quality_entity,
        "value": round(r_squared, 3)
    }, False)
    
except Exception as e:
    logger.warning(f"Błąd aktualizacji encji: {e}")

# Sprawdź jakość regresji i wyśli ostrzeżenie jeśli potrzeba
if r_squared < 0.4:
    logger.warning(f"Niska jakość regresji dla {room_id} (R²={r_squared:.3f}). Sprawdź pozycjonowanie czujnika lux.")
    
if abs(a) < 0.01:
    logger.warning(f"Bardzo mały współczynnik kierunkowy ({a:.4f}). Sprawdź czy czujnik reaguje na zmiany światła.")