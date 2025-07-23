import math

room_id = data.get("room_id")
if not room_id:
    logger.error("Brak 'room_id' w danych wejściowych")
    exit()

sample_entity = f"input_text.brightness_lux_samples_{room_id}"
regression_entity = f"input_text.brightness_regression_{room_id}"
quality_entity = f"input_number.regression_quality_{room_id}"

samples_raw = state.get(sample_entity)
if not samples_raw:
    logger.warning(f"Brak danych w {sample_entity}")
    exit()

# Parsujemy próbki - poprawiony format dla spójności
samples_parts = [s.strip() for s in samples_raw.strip(";").split(";") if s.strip()]
brightness_vals = []
lux_vals = []

for sample in samples_parts:
    if ":" not in sample:
        continue
    try:
        brightness_str, lux_str = sample.split(":", 1)
        brightness = float(brightness_str)
        lux = float(lux_str)
        
        # Walidacja danych
        if not (0 <= brightness <= 255):
            logger.warning(f"Nieprawidłowa jasność: {brightness}, pomijam próbkę")
            continue
        if lux < 0 or lux > 10000:  # Rozsądny zakres dla lux
            logger.warning(f"Nieprawidłowa wartość lux: {lux}, pomijam próbkę")
            continue
            
        brightness_vals.append(brightness)
        lux_vals.append(lux)
    except (ValueError, AttributeError) as e:
        logger.warning(f"Błąd parsowania próbki '{sample}': {e}")
        continue

n = len(brightness_vals)
if n < 5:  # Zwiększony minimalny requirement
    logger.warning(f"Za mało prawidłowych danych do regresji: {n} (minimum 5)")
    exit()

# Filtruj outliery - usuń próbki które są więcej niż 2 odchylenia standardowe od średniej
def remove_outliers(x_vals, y_vals):
    if len(x_vals) < 8:  # Nie filtruj gdy mało danych
        return x_vals, y_vals
    
    # Oblicz średnie i odchylenia standardowe
    x_mean = sum(x_vals) / len(x_vals)
    y_mean = sum(y_vals) / len(y_vals)
    x_std = math.sqrt(sum((x - x_mean) ** 2 for x in x_vals) / len(x_vals))
    y_std = math.sqrt(sum((y - y_mean) ** 2 for y in y_vals) / len(y_vals))
    
    # Filtruj
    filtered_x, filtered_y = [], []
    outliers_count = 0
    for x, y in zip(x_vals, y_vals):
        if (abs(x - x_mean) < 2 * x_std and abs(y - y_mean) < 2 * y_std):
            filtered_x.append(x)
            filtered_y.append(y)
        else:
            outliers_count += 1
    
    if outliers_count > 0:
        logger.info(f"Usunięto {outliers_count} outlierów z analizy")
    
    return filtered_x, filtered_y

brightness_vals, lux_vals = remove_outliers(brightness_vals, lux_vals)
n = len(brightness_vals)

if n < 3:
    logger.warning("Za mało danych po filtrowaniu outlierów")
    exit()

# Regresja liniowa: lux = a * brightness + b (przewidujemy lux na podstawie jasności)
x_vals = brightness_vals  # brightness jako zmienna niezależna
y_vals = lux_vals        # lux jako zmienna zależna

x_avg = sum(x_vals) / n
y_avg = sum(y_vals) / n

numerator = sum((x - x_avg) * (y - y_avg) for x, y in zip(x_vals, y_vals))
denominator = sum((x - x_avg) ** 2 for x in x_vals)

if denominator == 0:
    logger.warning("Wszystkie wartości jasności są identyczne - nie można wyliczyć regresji")
    exit()

a = numerator / denominator  # Współczynnik kierunkowy
b = y_avg - a * x_avg       # Wyraz wolny

# Oblicz jakość regresji (R²)
y_pred = [a * x + b for x in x_vals]
ss_res = sum((y_actual - y_pred) ** 2 for y_actual, y_pred in zip(y_vals, y_pred))
ss_tot = sum((y - y_avg) ** 2 for y in y_vals)

r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

# Oblicz korelację Pearsona
correlation = numerator / (math.sqrt(sum((x - x_avg) ** 2 for x in x_vals)) * 
                          math.sqrt(sum((y - y_avg) ** 2 for y in y_vals))) if denominator > 0 else 0

logger.info(f"Regresja dla {room_id}: a={a:.4f}, b={b:.1f}, R²={r_squared:.3f}, korelacja={correlation:.3f}, próbek={n}")

# Sprawdź czy regresja ma sens
if r_squared < 0.3:
    logger.warning(f"Niska jakość regresji (R²={r_squared:.3f}). Może nie ma liniowej zależności między jasnością a lux.")

if abs(correlation) < 0.5:
    logger.warning(f"Słaba korelacja ({correlation:.3f}). Sprawdź czy czujnik lux działa poprawnie.")

# Zapisz wyniki
regression_str = f"a:{round(a, 4)};b:{round(b, 1)};r2:{round(r_squared, 3)};n:{n}"

service.call("input_text", "set_value", {
    "entity_id": regression_entity,
    "value": regression_str
})

# Opcjonalnie zapisz jakość regresji jako osobną encję
try:
    service.call("input_number", "set_value", {
        "entity_id": quality_entity,
        "value": round(r_squared, 3)
    })
except:
    logger.debug("Brak encji input_number.regression_quality - tworzenie opcjonalne")