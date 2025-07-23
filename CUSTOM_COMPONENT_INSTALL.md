# 🚀 CUSTOM COMPONENT - Prosty Sposób Instalacji!

## 🎯 Dlaczego Custom Component?

**Zamiast kopiować 8 plików i modyfikować configuration.yaml, wystarczy:**
1. Skopiować 1 folder
2. Restart HA  
3. Dodać integrację przez UI
4. **GOTOWE!** 🎉

## 📦 Instalacja

### Metoda 1: HACS (Rekomendowana)
```
1. HACS → Integrations → Custom repositories
2. Dodaj URL: https://github.com/MuchaZ/smart-lights-control
3. Kategoria: Integration
4. Install → Restart HA
```

### Metoda 2: Ręczna instalacja
```bash
# W folderze config Home Assistant:
mkdir -p custom_components
cp -r smart_lux_control custom_components/
```

### Metoda 3: Lokalnie (z tego folderu)
```bash
# Skopiuj z obecnego folderu do HA:
cp -r smart_lux_control /config/custom_components/
```

## ⚡ Konfiguracja (SUPER PROSTA!)

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
- **Room Name**: `garderoba_master` (lub twoja nazwa)
- **Light Entity**: Wybierz swoją lampę
- **Lux Sensor**: Wybierz czujnik lux  
- **Motion Sensor**: Wybierz czujnik ruchu
- **Home Mode Select**: (Opcjonalnie) input_select z trybami

### 4. Kliknij Submit
**I to wszystko! 🎉**

## 🧠 Co dostaniesz automatycznie?

### Sensory (bez konfiguracji!):
- `sensor.ROOM_regression_quality` - Jakość regresji (R²)
- `sensor.ROOM_sample_count` - Liczba próbek
- `sensor.ROOM_smart_mode_status` - Status (Smart/Fallback/Learning)
- `sensor.ROOM_predicted_lux` - Przewidywane lux
- `sensor.ROOM_average_error` - Błąd przewidywań

### Przełączniki:
- `switch.ROOM_smart_mode` - Włącz/wyłącz smart mode
- `switch.ROOM_adaptive_learning` - Włącz/wyłącz adaptacyjne uczenie

### Serwisy:
- `smart_lux_control.calculate_regression` - Przelicz regresję
- `smart_lux_control.clear_samples` - Wyczyść próbki
- `smart_lux_control.add_sample` - Dodaj próbkę ręcznie
- `smart_lux_control.adaptive_learning` - Uruchom adaptacyjne uczenie

## 🎯 Jak używać w praktyce?

### W automatyzacji (przykład):
```yaml
alias: "Smart Light Control - Garderoba"
trigger:
  - platform: state
    entity_id: binary_sensor.garderoba_motion
    to: "on"
  - platform: time_pattern
    seconds: "/30"
action:
  - if:
      - condition: state
        entity_id: switch.garderoba_master_smart_mode
        state: "on"
    then:
      # Smart mode - precyzyjne obliczenia
      - service: light.turn_on
        target:
          entity_id: light.garderoba
        data:
          brightness: >
            {% set coordinator = states.sensor.garderoba_master_sample_count %}
            {% set target_lux = 300 %}
            {% set current_brightness = state_attr('light.garderoba', 'brightness') | int(255) %}
            {{ coordinator.calculate_target_brightness(target_lux, current_brightness) }}
    else:
      # Fallback mode
      - service: light.turn_on
        target:
          entity_id: light.garderoba
        data:
          brightness: 150
```

### Przeliczanie regresji:
```yaml
service: smart_lux_control.calculate_regression
data:
  room_name: "garderoba_master"
```

## 📊 Monitoring

### Dashboard (automatyczne sensory):
```yaml
type: entities
entities:
  - sensor.garderoba_master_smart_mode_status
  - sensor.garderoba_master_regression_quality
  - sensor.garderoba_master_sample_count
  - sensor.garderoba_master_predicted_lux
  - switch.garderoba_master_smart_mode
  - switch.garderoba_master_adaptive_learning
```

## 🔧 Zaawansowane ustawienia

```
Settings → Devices & Services → Smart Lux Control → Options
```

Możesz dostosować:
- **Min Regression Quality**: Próg jakości dla smart mode (domyślnie 0.5)
- **Max Brightness Change**: Maksymalna zmiana jasności (domyślnie 50)
- **Deviation Margin**: Tolerancja różnicy lux (domyślnie 15)
- **Learning Rate**: Szybkość adaptacyjnego uczenia (domyślnie 0.1)

## ✅ Korzyści Custom Component

| Aspekt | Multi-file (stare) | Custom Component (nowe) |
|--------|-------------------|-------------------------|
| **Instalacja** | 8 plików + config | 1 folder + UI |
| **Konfiguracja** | Ręczne YAML | Graficzny interfejs |
| **Encje** | Ręczne tworzenie | Automatyczne |
| **Aktualizacje** | Ręczne kopiowanie | HACS one-click |
| **Debugging** | Trudne | Sensory + logi |
| **Multi-room** | Powielanie config | Dodaj kolejną integrację |

## 🎉 Rezultat

**Zamiast 30 minut konfiguracji i modyfikowania plików, masz:**
- ⚡ 2 minuty instalacji
- 🖱️ Konfiguracja przez GUI  
- 📊 Automatyczne sensory
- 🔄 Łatwe aktualizacje
- 🏠 Multi-room support

**To jest ZNACZNIE lepsze rozwiązanie! 🚀** 