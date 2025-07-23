"""
Adaptacyjne uczenie się dla systemu regresji jasności.
Ten skrypt automatycznie poprawia model regresji na podstawie rzeczywistych wyników.

Uruchamiany okresowo lub po znaczących zmianach w danych.
"""

import math
from datetime import datetime, timedelta

# Pobierz parametry
room_id = data.get("room_id")
learning_rate = data.get("learning_rate", 0.1)
min_samples_for_update = data.get("min_samples_for_update", 10)

if not room_id:
    logger.error("Brak room_id dla adaptacyjnego uczenia")
    exit()

logger.info(f"Adaptacyjne uczenie dla {room_id}, learning_rate={learning_rate}")

# Encje
samples_entity = f"input_text.brightness_lux_samples_{room_id}"
regression_entity = f"input_text.brightness_regression_{room_id}"
a_entity = f"input_number.light_regression_a_{room_id}"
b_entity = f"input_number.light_regression_b_{room_id}"
quality_entity = f"input_number.regression_quality_{room_id}"
history_entity = f"input_text.adaptive_history_{room_id}"

# Pobierz obecne współczynniki regresji
current_a = float(hass.states.get(a_entity).state) if hass.states.get(a_entity) else 1.0
current_b = float(hass.states.get(b_entity).state) if hass.states.get(b_entity) else 0.0
current_quality = float(hass.states.get(quality_entity).state) if hass.states.get(quality_entity) else 0.0

# Pobierz próbki
samples_raw = hass.states.get(samples_entity)
if not samples_raw or samples_raw.state in ['unknown', 'unavailable', '']:
    logger.warning(f"Brak danych próbek w {samples_entity}")
    exit()

# Parsuj próbki
samples_parts = [s.strip() for s in samples_raw.state.strip(";").split(";") if s.strip()]
brightness_vals = []
lux_vals = []
timestamps = []

for sample in samples_parts:
    if ":" not in sample:
        continue
    
    # Może mieć timestamp: "brightness:lux#timestamp"
    if "#" in sample:
        sample_data, timestamp_str = sample.split("#", 1)
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M")
            timestamps.append(timestamp)
        except:
            timestamps.append(datetime.now())
    else:
        sample_data = sample
        timestamps.append(datetime.now())
    
    try:
        brightness_str, lux_str = sample_data.split(":", 1)
        brightness = float(brightness_str)
        lux = float(lux_str)
        
        # Walidacja
        if 0 <= brightness <= 255 and 0 <= lux <= 10000:
            brightness_vals.append(brightness)
            lux_vals.append(lux)
        else:
            timestamps.pop()  # Usuń timestamp dla nieprawidłowej próbki
    except:
        if timestamps:
            timestamps.pop()  # Usuń timestamp dla nieprawidłowej próbki
        continue

n = len(brightness_vals)
if n < min_samples_for_update:
    logger.info(f"Za mało próbek dla adaptacyjnego uczenia: {n}/{min_samples_for_update}")
    exit()

# Analizuj czasowe trendy - nowsze próbki mają większą wagę
now = datetime.now()
weights = []
for timestamp in timestamps:
    age_hours = (now - timestamp).total_seconds() / 3600
    # Waga maleje wykładniczo z czasem (half-life = 24h)
    weight = math.exp(-age_hours / 24.0)
    weights.append(weight)

# Sprawdź czy są znaczące różnice między przewidywaniami a rzeczywistością
errors = []
for brightness, lux in zip(brightness_vals, lux_vals):
    predicted_lux = current_a * brightness + current_b
    error = abs(lux - predicted_lux)
    errors.append(error)

average_error = sum(errors) / len(errors)
max_error = max(errors)

logger.info(f"Analiza błędów: średni={average_error:.2f}lx, max={max_error:.2f}lx")

# Decyzja czy aktualizować model
should_update = False
update_reason = ""

if average_error > 20:  # Średni błąd > 20 lux
    should_update = True
    update_reason = f"Duży średni błąd: {average_error:.1f}lx"
elif max_error > 50:  # Maksymalny błąd > 50 lux
    should_update = True
    update_reason = f"Duży maksymalny błąd: {max_error:.1f}lx"
elif current_quality < 0.7 and n >= 20:  # Niska jakość ale dużo danych
    should_update = True
    update_reason = f"Niska jakość R²={current_quality:.3f} z {n} próbkami"

if not should_update:
    logger.info("Model jest wystarczająco dobry, brak potrzeby aktualizacji")
    exit()

logger.info(f"Aktualizacja modelu: {update_reason}")

# Oblicz nową regresję z wagami
def weighted_regression(x_vals, y_vals, weights):
    """Oblicz regresję liniową z wagami"""
    n = len(x_vals)
    sum_w = sum(weights)
    
    # Średnie ważone
    x_avg = sum(w * x for w, x in zip(weights, x_vals)) / sum_w
    y_avg = sum(w * y for w, y in zip(weights, y_vals)) / sum_w
    
    # Oblicz współczynniki
    numerator = sum(w * (x - x_avg) * (y - y_avg) for w, x, y in zip(weights, x_vals, y_vals))
    denominator = sum(w * (x - x_avg) ** 2 for w, x in zip(weights, x_vals))
    
    if denominator == 0:
        return None, None, 0
    
    a = numerator / denominator
    b = y_avg - a * x_avg
    
    # Oblicz R² ważone
    y_pred = [a * x + b for x in x_vals]
    ss_res = sum(w * (y_actual - y_pred) ** 2 for w, y_actual, y_pred in zip(weights, y_vals, y_pred))
    ss_tot = sum(w * (y - y_avg) ** 2 for w, y in zip(weights, y_vals))
    
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    return a, b, r_squared

# Oblicz nową regresję
new_a, new_b, new_r_squared = weighted_regression(brightness_vals, lux_vals, weights)

if new_a is None:
    logger.warning("Nie można obliczyć nowej regresji")
    exit()

# Adaptacyjna aktualizacja - mieszaj stary model z nowym
adaptive_a = current_a * (1 - learning_rate) + new_a * learning_rate
adaptive_b = current_b * (1 - learning_rate) + new_b * learning_rate

# Sprawdź czy nowy model jest sensowny
if abs(adaptive_a) > 10 or abs(adaptive_b) > 1000:
    logger.warning(f"Nowe współczynniki wydają się nieprawdopodobne: a={adaptive_a:.4f}, b={adaptive_b:.1f}")
    exit()

# Porównaj jakość
improvement = new_r_squared - current_quality
logger.info(f"Stary model: a={current_a:.4f}, b={current_b:.1f}, R²={current_quality:.3f}")
logger.info(f"Nowy model: a={new_a:.4f}, b={new_b:.1f}, R²={new_r_squared:.3f}")
logger.info(f"Adaptacyjny model: a={adaptive_a:.4f}, b={adaptive_b:.1f}, poprawa R²={improvement:.3f}")

# Aktualizuj współczynniki
try:
    hass.services.call("input_number", "set_value", {
        "entity_id": a_entity,
        "value": round(adaptive_a, 4)
    }, False)

    hass.services.call("input_number", "set_value", {
        "entity_id": b_entity,
        "value": round(adaptive_b, 1)
    }, False)
    
    hass.services.call("input_number", "set_value", {
        "entity_id": quality_entity,
        "value": round(new_r_squared, 3)
    }, False)

    # Zaktualizuj string regresji
    regression_str = f"a:{round(adaptive_a, 4)};b:{round(adaptive_b, 1)};r2:{round(new_r_squared, 3)};n:{n};adaptive:true"
    hass.services.call("input_text", "set_value", {
        "entity_id": regression_entity,
        "value": regression_str
    }, False)
    
    # Zapisz historię adaptacji
    history_entry = f"{datetime.now().strftime('%Y%m%d_%H%M')}:a={adaptive_a:.4f}:b={adaptive_b:.1f}:r2={new_r_squared:.3f}:reason={update_reason}"
    
    current_history = hass.states.get(history_entity)
    if current_history and current_history.state not in ['unknown', 'unavailable', '']:
        history_list = current_history.state.split(';')
    else:
        history_list = []
    
    history_list.append(history_entry)
    history_list = history_list[-20:]  # Zachowaj ostatnie 20 wpisów
    
    hass.states.set(history_entity, ';'.join(history_list))
    
    logger.info(f"✅ Adaptacyjna aktualizacja zakończona dla {room_id}")
    
except Exception as e:
    logger.error(f"Błąd aktualizacji encji: {e}")

# Sprawdź czy model się pogorszył znacząco
if improvement < -0.1:
    logger.warning(f"Jakość modelu znacząco spadła! Rozważ powrót do poprzedniej wersji.")

# Wyślij powiadomienie o znaczącej poprawie
if improvement > 0.1:
    try:
        hass.services.call("notify", "persistent_notification", {
            "title": "🧠 Adaptacyjne Uczenie",
            "message": f"Model regresji dla {room_id} został ulepszony! R² wzrosło z {current_quality:.3f} do {new_r_squared:.3f}. {update_reason}"
        }, False)
    except:
        pass  # Jeśli notify nie działa, nie przejmuj się 