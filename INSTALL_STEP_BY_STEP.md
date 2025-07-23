# 📋 Instrukcja Instalacji Krok po Krok

## 🎯 Cel
Zainstalować inteligentny system zarządzania światłem w Home Assistant.

## ⚠️ Wymagania
- Home Assistant Core/Supervised/OS
- Włączony `python_script:` w konfiguracji
- Czujnik lux
- Światło z regulacją jasności
- Czujnik ruchu

---

## 🚀 KROK 1: Przygotowanie plików Python

### 1.1 Sprawdź czy masz folder python_scripts
```bash
# W folderze config HA
ls -la | grep python_scripts
```

### 1.2 Jeśli nie ma, utwórz go
```bash
mkdir python_scripts
```

### 1.3 Skopiuj pliki Python
```bash
# Z tego folderu do HA:
cp calculate_brightness_regression.py /config/python_scripts/
cp learn_brightness_lux.py /config/python_scripts/
cp adaptive_learning.py /config/python_scripts/
```

### 1.4 Sprawdź uprawnienia
```bash
chmod 644 /config/python_scripts/*.py
```

---

## 🚀 KROK 2: Konfiguracja w configuration.yaml

### 2.1 Włącz python_script (jeśli nie masz)
```yaml
# W configuration.yaml dodaj:
python_script:
```

### 2.2 Dodaj encje dla swojego pokoju
**Zmień `garderoba_master` na nazwę swojego pokoju!**

```yaml
# Dodaj to do configuration.yaml:
input_text:
  brightness_lux_samples_TWOJA_NAZWA_POKOJU:
    name: "Próbki brightness→lux TWÓJ POKÓJ"
    max: 3000
    initial: ""

  brightness_regression_TWOJA_NAZWA_POKOJU:
    name: "Regresja brightness→lux TWÓJ POKÓJ"
    max: 300
    initial: "a:1;b:0;r2:0;n:0"

  last_sample_TWOJA_NAZWA_POKOJU:
    name: "Ostatnia próbka TWÓJ POKÓJ"
    max: 50
    initial: ""

  adaptive_history_TWOJA_NAZWA_POKOJU:
    name: "Historia adaptacji TWÓJ POKÓJ"
    max: 1000
    initial: ""

input_number:
  light_regression_a_TWOJA_NAZWA_POKOJU:
    name: "Współczynnik A - TWÓJ POKÓJ"
    min: -100
    max: 100
    step: 0.0001
    initial: 1

  light_regression_b_TWOJA_NAZWA_POKOJU:
    name: "Współczynnik B - TWÓJ POKÓJ"
    min: -1000
    max: 1000
    step: 0.01
    initial: 0

  regression_quality_TWOJA_NAZWA_POKOJU:
    name: "Jakość regresji R² - TWÓJ POKÓJ"
    min: 0
    max: 1
    step: 0.001
    initial: 0

input_datetime:
  last_sample_time_TWOJA_NAZWA_POKOJU:
    name: "Czas ostatniej próbki - TWÓJ POKÓJ"
    has_date: true
    has_time: true

input_boolean:
  smart_mode_enabled_TWOJA_NAZWA_POKOJU:
    name: "Smart Mode włączony - TWÓJ POKÓJ"
    initial: true

  adaptive_learning_enabled_TWOJA_NAZWA_POKOJU:
    name: "Adaptacyjne uczenie włączone - TWÓJ POKÓJ"
    initial: true

# Tryb domu (jeśli nie masz)
input_select:
  home_mode:
    name: "Tryb domu"
    options:
      - normal
      - noc
      - impreza
      - relaks
      - film
      - sprzatanie
      - dziecko_spi
    initial: normal
```

---

## 🚀 KROK 3: Restart Home Assistant

```
Settings → System → Restart → Restart Home Assistant
```

**Poczekaj aż HA się zrestartuje!**

---

## 🚀 KROK 4: Sprawdź czy encje zostały utworzone

### 4.1 Przejdź do Developer Tools → States
### 4.2 Szukaj encji z nazwą swojego pokoju:
- `input_text.brightness_lux_samples_TWOJA_NAZWA`
- `input_number.light_regression_a_TWOJA_NAZWA`
- `input_boolean.smart_mode_enabled_TWOJA_NAZWA`

**Jeśli nie ma - sprawdź błędy w konfiguracji!**

---

## 🚀 KROK 5: Import blueprintów

### 5.1 Zbieranie danych (learn.yaml)
1. Settings → Automations & Scenes → Blueprints
2. Import Blueprint → wklej URL lub importuj `learn.yaml`
3. Create automation from blueprint
4. Konfiguruj:
   - **Light target**: Twoje światło
   - **Sensor lux**: Twój czujnik lux
   - **Room ID**: `TWOJA_NAZWA_POKOJU` (dokładnie jak w config!)
   - **Motion sensor**: Twój czujnik ruchu

### 5.2 Smart sterowanie (lux_control_smart.yaml)
1. Import Blueprint → `lux_control_smart.yaml`
2. Create automation from blueprint
3. Konfiguruj:
   - **Room ID**: `TWOJA_NAZWA_POKOJU` (identyczne jak wyżej!)
   - **Light target**: Twoje światło
   - **Sensor lux**: Twój czujnik lux
   - **Motion sensor**: Twój czujnik ruchu
   - **Home mode**: `input_select.home_mode`

---

## 🚀 KROK 6: Testowanie systemu

### 6.1 Zbieranie próbek (pierwsze 2-3 dni)
1. Włącz/wyłącz światło kilka razy
2. Zmieniaj jasność ręcznie (10%, 50%, 100%)
3. Sprawdzaj w Developer Tools → States:
   - `input_text.brightness_lux_samples_TWOJA_NAZWA` - czy zbiera próbki

### 6.2 Sprawdzenie regresji
Po zebraniu ~10 próbek:
```yaml
# Developer Tools → Services
service: python_script.calculate_brightness_regression
data:
  room_id: "TWOJA_NAZWA_POKOJU"
```

### 6.3 Sprawdź jakość
```yaml
# Sprawdź w States:
input_number.regression_quality_TWOJA_NAZWA_POKOJU
```
- Wartość > 0.5 = Smart Mode będzie działać
- Wartość < 0.5 = Potrzebujesz więcej próbek

---

## 🚀 KROK 7: Monitoring (opcjonalnie)

### 7.1 Dodaj sensory do monitoringu
```yaml
# W configuration.yaml:
sensor:
  - platform: template
    sensors:
      smart_status_TWOJA_NAZWA:
        friendly_name: "Status Smart Mode"
        value_template: >
          {% set quality = states('input_number.regression_quality_TWOJA_NAZWA_POKOJU') | float(0) %}
          {% if quality >= 0.5 %}Smart Active{% else %}Fallback Mode{% endif %}
        icon_template: >
          {% set quality = states('input_number.regression_quality_TWOJA_NAZWA_POKOJU') | float(0) %}
          {% if quality >= 0.5 %}mdi:brain{% else %}mdi:cog-outline{% endif %}
```

### 7.2 Dodaj do dashboard
Karta monitoring:
- `input_number.regression_quality_TWOJA_NAZWA_POKOJU`
- `sensor.smart_status_TWOJA_NAZWA`
- `input_text.brightness_lux_samples_TWOJA_NAZWA_POKOJU`

---

## 🔧 Troubleshooting

### Problem: Smart Mode nie włącza się
**Rozwiązanie:**
1. Sprawdź `input_number.regression_quality_TWOJA_NAZWA` - musi być > 0.5
2. Zbierz więcej próbek (różne jasności w różnych warunkach)
3. Sprawdź logi: Settings → System → Logs

### Problem: Błędne próbki
**Rozwiązanie:**
1. Wyczyść próbki: ustaw `input_text.brightness_lux_samples_TWOJA_NAZWA` na ""
2. Sprawdź czy czujnik lux działa poprawnie
3. Upewnij się że światło wpływa na czujnik

### Problem: Automatyzacje nie działają
**Rozwiązanie:**
1. Sprawdź czy `room_id` w automatyzacjach = nazwa w konfiguracji
2. Sprawdź czy wszystkie encje istnieją
3. Sprawdź triggery (ruch, time_pattern)

---

## ✅ Sukces!

**Gdy wszystko działa:**
- Smart Mode pokazuje "Smart Active"
- Światło reaguje precyzyjnie na zmiany trybu
- Jakość regresji R² > 0.7
- Logi pokazują: `🧠 SMART: [room] | Docelowe: [X]lx | Jasność: [A]→[B]`

**🎉 Gratulacje! Masz inteligentne światło! 🎉** 