# 🧠 Smart Lights Control for Home Assistant

[![GitHub release](https://img.shields.io/github/release/MuchaZ/smart-lights-control.svg)](https://github.com/MuchaZ/smart-lights-control/releases)
[![GitHub stars](https://img.shields.io/github/stars/MuchaZ/smart-lights-control.svg)](https://github.com/MuchaZ/smart-lights-control/stargazers)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-compatible-blue.svg)](https://www.home-assistant.io/)
[![HACS](https://img.shields.io/badge/HACS-compatible-orange.svg)](https://hacs.xyz/)

**Inteligentny system zarządzania oświetleniem używający regresji liniowej i adaptacyjnego uczenia maszynowego.**

Zamiast ślepego zmieniania jasności o stały krok, system oblicza **precyzyjnie** jaką jasność ustawić żeby osiągnąć docelowy poziom lux.

## 🎯 Główne zalety

- ⚡ **Natychmiastowe reakcje** - 1 precyzyjna korekta zamiast 3-5 prób
- 🎯 **Wysoka dokładność** - ±10lx zamiast ±50lx tolerancji  
- 🧠 **Samodoskonalenie** - system uczy się z każdą zmianą
- 📊 **Pełny monitoring** - sensory jakości regresji i statusu
- 🛡️ **Zabezpieczenia** - fallback gdy regresja niedokładna

## 🚀 Przed i Po

### PRZED (stary system):
```
Docelowe: 300lx, Obecne: 200lx
❌ Dodaj +20 brightness (na ślepo)
❌ Czekaj i sprawdź... może dodaj kolejne +20
❌ Może jeszcze +20? Jak długo to będzie trwać?
```

### PO (smart system):
```
Docelowe: 300lx, Obecne: 200lx
🧠 Regresja: lux = 2.5 * brightness + 15
🧠 Potrzebuję: (300-15)/2.5 = 114 brightness
✅ Ustaw natychmiast 114 brightness = dokładnie 300lx!
```

## 📦 Instalacja

### Metoda 1: HACS (Rekomendowana)

1. **HACS** → **Integrations** → **Custom repositories**
2. Dodaj URL: `https://github.com/MuchaZ/smart-lights-control`
3. Kategoria: **Integration**
4. **Install** → **Restart HA**

### Metoda 2: Ręczna instalacja

```bash
# W folderze config Home Assistant:
cd /config
git clone https://github.com/MuchaZ/smart-lights-control.git
cp -r smart-lights-control/custom_components/smart_lux_control custom_components/
```

## ⚡ Konfiguracja

### 1. Restart Home Assistant
```
Settings → System → Restart
```

### 2. Dodaj integrację
```
Settings → Devices & Services → Add Integration
→ Szukaj: "Smart Lux Control"
```

### 3. Wypełnij formularz
- **Room Name**: `living_room` (nazwa pokoju)
- **Light Entity**: Wybierz swoją lampę
- **Lux Sensor**: Wybierz czujnik lux  
- **Motion Sensor**: Wybierz czujnik ruchu
- **Home Mode Select**: (Opcjonalnie) input_select z trybami domu

### 4. Gotowe! 🎉

## 🧠 Co dostajesz automatycznie

### Sensory (bez dodatkowej konfiguracji!)
- `sensor.ROOM_regression_quality` - Jakość regresji (R²)
- `sensor.ROOM_sample_count` - Liczba próbek w systemie
- `sensor.ROOM_smart_mode_status` - Status (Smart/Fallback/Learning)
- `sensor.ROOM_predicted_lux` - Przewidywane lux dla obecnej jasności
- `sensor.ROOM_average_error` - Średni błąd przewidywań

### Przełączniki
- `switch.ROOM_smart_mode` - Włącz/wyłącz smart mode
- `switch.ROOM_adaptive_learning` - Włącz/wyłącz adaptacyjne uczenie

### Serwisy
- `smart_lux_control.calculate_regression` - Przelicz regresję
- `smart_lux_control.clear_samples` - Wyczyść próbki
- `smart_lux_control.add_sample` - Dodaj próbkę ręcznie
- `smart_lux_control.adaptive_learning` - Uruchom adaptacyjne uczenie

## 🎯 Przykład użycia

### Automatyzacja z inteligentnym sterowaniem:

```yaml
alias: "Smart Light Control - Living Room"
trigger:
  - platform: state
    entity_id: binary_sensor.living_room_motion
    to: "on"
  - platform: time_pattern
    seconds: "/30"
condition:
  - condition: state
    entity_id: switch.living_room_smart_mode
    state: "on"
action:
  - service: smart_lux_control.calculate_target_brightness
    data:
      room_name: "living_room"
      target_lux: 300
    response_variable: target_brightness
  - service: light.turn_on
    target:
      entity_id: light.living_room
    data:
      brightness: "{{ target_brightness.brightness }}"
      transition: 2
```

### Monitoring jakości regresji:

```yaml
# Automatyczne powiadomienie o niskiej jakości
automation:
  - alias: "Ostrzeżenie o słabej regresji"
    trigger:
      - platform: numeric_state
        entity_id: sensor.living_room_regression_quality
        below: 0.4
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ Słaba jakość regresji"
          message: "System światła w {{ trigger.to_state.name }} potrzebuje więcej próbek"
```

## 📊 Dashboard

Dodaj karty do monitorowania:

```yaml
type: entities
title: Smart Light Control - Living Room
entities:
  - sensor.living_room_smart_mode_status
  - sensor.living_room_regression_quality
  - sensor.living_room_sample_count
  - sensor.living_room_predicted_lux
  - switch.living_room_smart_mode
  - switch.living_room_adaptive_learning
```

## 🔧 Zaawansowane ustawienia

```
Settings → Devices & Services → Smart Lux Control → Options
```

Dostosuj parametry:
- **Min Regression Quality**: Próg jakości dla smart mode (domyślnie 0.5)
- **Max Brightness Change**: Maksymalna zmiana jasności za jednym razem (domyślnie 50)
- **Deviation Margin**: Tolerancja różnicy lux (domyślnie 15)
- **Learning Rate**: Szybkość adaptacyjnego uczenia (domyślnie 0.1)

## 🧪 Jak to działa

### 1. Zbieranie danych
System automatycznie zbiera pary `brightness → lux` gdy zmieniasz światło.

### 2. Regresja liniowa
Oblicza równanie: `lux = a × brightness + b`

### 3. Smart obliczenia
Gdy potrzebujesz konkretnego poziomu lux, system używa wzoru:
`brightness = (target_lux - b) / a`

### 4. Adaptacyjne uczenie
System regularnie poprawia model na podstawie nowych danych.

### 5. Zabezpieczenia
Gdy regresja jest niedokładna (R² < 0.5), system przełącza się na tryb awaryjny.

## 📈 Interpretacja R² (jakości regresji)

- **R² > 0.8** 🟢 - Doskonała jakość, smart mode w pełni aktywny
- **R² 0.5-0.8** 🟡 - Dobra jakość, smart mode działa dobrze  
- **R² < 0.5** 🔴 - Słaba jakość, system używa trybu awaryjnego

## 🔧 Troubleshooting

### Smart Mode nie włącza się
1. Sprawdź `sensor.ROOM_regression_quality` - musi być > 0.5
2. Zbierz więcej próbek (różne jasności w różnych warunkach)
3. Sprawdź czy czujnik lux reaguje na zmiany światła

### Nieprawidłowe przewidywania
1. Wyczyść próbki: `smart_lux_control.clear_samples`
2. Sprawdź pozycjonowanie czujnika lux
3. Upewnij się że światło wpływa na czujnik

### Brak próbek
1. Sprawdź czy automatyzacja działa
2. Włącz/wyłącz światło kilka razy ręcznie
3. Zmień jasność w różnych zakresach (10%, 50%, 100%)

## 🏠 Multi-room

Dla każdego pokoju po prostu dodaj kolejną integrację:
```
Settings → Devices & Services → Add Integration → Smart Lux Control
```

Każdy pokój ma własne:
- Sensory (`sensor.ROOM_regression_quality`)
- Przełączniki (`switch.ROOM_smart_mode`)
- Model regresji (niezależny od innych)

## 🤝 Współpraca

Zgłoś błędy, sugestie lub pull requesty na [GitHub Issues](https://github.com/MuchaZ/smart-lights-control/issues).

## 📜 Licencja

MIT License - zobacz [LICENSE](LICENSE) plik.

## ⭐ Wsparcie

Jeśli ten projekt Ci pomógł, zostaw ⭐ na GitHubie!

---

**Twoje światło jest teraz naprawdę inteligentne! 🧠💡** 