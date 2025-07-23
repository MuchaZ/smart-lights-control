# 🌟 Smart Lux Control for Home Assistant

**Inteligentne sterowanie oświetleniem z regresją liniową i automatycznym uczeniem się**

Zaawansowany custom component do Home Assistant, który automatycznie steruje jasnością światła na podstawie docelowych poziomów lux, wykorzystując regresję liniową i adaptacyjne uczenie się.

## ✨ **Główne funkcje**

### 🧠 **Smart Mode**
- **Regresja liniowa**: Precyzyjne obliczanie jasności na podstawie modelu matematycznego
- **Automatyczne uczenie**: Zbieranie próbek i budowanie modelu brightness ↔ lux
- **Jakość predykcji**: Wskaźnik R² pokazuje dokładność modelu

### 🏠 **Automatyczne sterowanie**
- **Detekcja ruchu**: Automatyczne włączanie światła gdy ktoś wchodzi
- **Timer**: Konfigurowalny czas świecenia po ostatnim ruchu  
- **Tryby domu**: Różne poziomy lux dla różnych aktywności
- **Dzień/noc**: Automatyczne przejścia bazowane na wschodzące/zachodzące słońce

### 📈 **Adaptacyjne uczenie**
- **Weighted regression**: Nowsze próbki mają większy wpływ na model
- **Exponential decay**: Starsze dane stopniowo tracą na znaczeniu
- **Outlier filtering**: Automatyczne filtrowanie błędnych pomiarów

### 🎛️ **Fallback mode**
- **Step adjustment**: Gdy model nie jest wystarczająco dobry
- **Bezpieczne sterowanie**: Zawsze działa, nawet bez regresji

## 🚀 **Instalacja**

### Przez HACS (Rekomendowane)

1. **Dodaj repository**: W HACS → Integracje → Menu (⋮) → Repozytoria niestandardowe
   ```
   https://github.com/MuchaZ/smart-lights-control
   ```

2. **Zainstaluj**: Wyszukaj "Smart Lux Control" i zainstaluj

3. **Restart Home Assistant**

4. **Dodaj integrację**: Ustawienia → Urządzenia i usługi → Dodaj integrację → "Smart Lux Control"

### Konfiguracja przez UI

Component ma **3-etapową konfigurację**:

#### **Krok 1/3: Podstawowa konfiguracja**
- **Nazwa pokoju**: Unikalna nazwa (np. `living_room`)
- **Lampy**: Wybierz jedną lub więcej lamp do sterowania
- **Czujnik lux**: Sensor illuminance (np. czujnik Xiaomi)
- **Czujnik ruchu**: Binary sensor motion
- **Tryb domu**: (Opcjonalnie) input_select z trybami
- **Auto sterowanie**: Włącz automatyczne sterowanie

#### **Krok 2/3: Ustawienia lux**
- **Normal dzień**: 400 lx (światło dzienne)
- **Normal noc**: 150 lx (wieczorem)  
- **Tryb noc**: 10 lx (nocne oświetlenie)
- **Tryb impreza**: 500 lx (jasno na przyjęcie)
- **Tryb relaks**: 120 lx (spokojny wieczór)
- **Tryb film**: 60 lx (oglądanie TV)
- **Tryb sprzątanie**: 600 lx (prace domowe)
- **Tryb dziecko śpi**: 8 lx (minimalne światło)

#### **Krok 3/3: Timing**
- **Czas świecenia**: 5 min (jak długo świecić po ruchu)
- **Bufor dzień/noc**: 30 min (płynne przejścia)
- **Tolerancja**: 15 lx (dopuszczalne odchylenie)
- **Sprawdzanie**: 30s (jak często sprawdzać warunki)

## 🎛️ **Encje**

Po instalacji otrzymujesz dla każdego pokoju:

### 🔘 **Switche**
- `switch.{pokój}_smart_mode` - Włącz/wyłącz tryb inteligentny
- `switch.{pokój}_adaptive_learning` - Włącz/wyłącz adaptacyjne uczenie  
- `switch.{pokój}_auto_control` - Włącz/wyłącz automatyczne sterowanie

### 📊 **Sensory**
- `sensor.{pokój}_regression_quality` - Jakość modelu (R²)
- `sensor.{pokój}_sample_count` - Liczba zebranych próbek
- `sensor.{pokój}_smart_mode_status` - Status trybu (Smart/Fallback/Learning)
- `sensor.{pokój}_predicted_lux` - Przewidywane lux dla aktualnej jasności
- `sensor.{pokój}_average_error` - Średni błąd predykcji
- `sensor.{pokój}_target_lux` - Aktualnie docelowe lux
- `sensor.{pokój}_automation_status` - Status automatyzacji (Active/Standby/Disabled)
- `sensor.{pokój}_last_automation_action` - Ostatnie działanie
- `sensor.{pokój}_motion_timer` - Pozostały czas do wyłączenia po ruchu

## 🛠️ **Serwisy**

### Zarządzanie próbkami
```yaml
# Ręczne dodanie próbki
service: smart_lux_control.add_sample
data:
  room_name: living_room
  brightness: 200
  lux: 450
```

```yaml
# Wyczyść wszystkie próbki
service: smart_lux_control.clear_samples
data:
  room_name: living_room
```

### Regresja i uczenie
```yaml
# Przelicz regresję
service: smart_lux_control.calculate_regression
data:
  room_name: living_room
```

```yaml
# Uruchom adaptacyjne uczenie
service: smart_lux_control.adaptive_learning
data:
  room_name: living_room
```

### Sterowanie jasności
```yaml
# Oblicz optymalną jasność dla docelowego lux
service: smart_lux_control.calculate_target_brightness
data:
  room_name: living_room
  target_lux: 300
  current_brightness: 255
```

## 📋 **Jak to działa**

### 1. **Faza uczenia** (pierwsze dni)
- Component zbiera próbki: brightness → lux measurement
- Automatycznie po każdej zmianie jasności lampy
- Minimum 5 próbek do uruchomienia smart mode

### 2. **Smart mode** (gdy model jest dobry)
- Używa regresji: `lux = a × brightness + b`
- Odwraca wzór: `brightness = (target_lux - b) / a`
- Precyzyjne sterowanie - dokładnie ta jasność, która da żądane lux

### 3. **Automatyczne sterowanie**
- Sprawdza co 30s (konfigurowalny)
- **Ruch wykryty** → Światło ON, docelowy lux bazowany na trybie domu i czasie
- **Brak ruchu 5 min** → Światło OFF
- **Smart mode**: Kalkuluje dokładną jasność
- **Fallback**: Zwiększa/zmniejsza jasność krokowo (+/-30)

### 4. **Adaptacyjne uczenie**
- Nowsze próbki mają większą wagę w modelu
- Eksponencjalny spadek wagi starszych danych
- Automatyczne usuwanie outlierów
- Model staje się lepszy z czasem

## 🏡 **Konfiguracja trybów domu**

Stwórz `input_select` z trybami:

```yaml
input_select:
  home_mode:
    name: Tryb domu
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

## 📊 **Dashboard**

Przykład karty Lovelace:

```yaml
type: entities
title: Smart Lux Control - Salon
entities:
  - entity: switch.salon_auto_control
    name: Automatyczne sterowanie
  - entity: switch.salon_smart_mode  
    name: Tryb inteligentny
  - entity: sensor.salon_automation_status
    name: Status automatyzacji
  - entity: sensor.salon_target_lux
    name: Docelowe lux
  - entity: sensor.salon_predicted_lux
    name: Aktualne lux (przewidywane)
  - entity: sensor.salon_regression_quality
    name: Jakość modelu
  - entity: sensor.salon_sample_count
    name: Próbki
  - entity: sensor.salon_motion_timer
    name: Timer ruchu
```

## 🔧 **Zaawansowane opcje**

W ustawieniach integracji możesz dostroić:
- **Minimalna jakość regresji**: 0.5 (kiedy używać smart mode)
- **Maksymalna zmiana jasności**: 50 (ograniczenie zmiany za jednym razem)
- **Szybkość uczenia**: 0.1 (jak szybko model się uczy)

## 🚨 **Rozwiązywanie problemów**

### Model nie uczy się
- Sprawdź czy czujnik lux działa: `sensor.{room}_predicted_lux`
- Poczekaj na więcej próbek: min. 5 dla smart mode, 15+ dla dobrej jakości
- Sprawdź logi: `grep "Smart Lux Control" home-assistant.log`

### Światła się nie włączają
- Sprawdź `switch.{room}_auto_control` - czy włączony?
- Sprawdź czujnik ruchu: `binary_sensor.{motion_sensor}`
- Sprawdź `sensor.{room}_automation_status` - powinien być "Active" przy ruchu

### Smart mode nie działa
- Sprawdź `sensor.{room}_regression_quality` - powinien być >0.5
- Sprawdź `sensor.{room}_smart_mode_status` - czy "Smart Active"?
- Jeśli "Fallback Mode" - zbierz więcej próbek lub zwiększ tolerancję

## 🤝 **Wkład w projekt**

1. Fork repository
2. Stwórz branch: `git checkout -b feature/amazing-feature`
3. Commit: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Otwórz Pull Request

## 📄 **Licencja**

MIT License - zobacz [LICENSE](LICENSE)

## ❤️ **Podziękowania**

- Home Assistant community
- HACS team
- Wszyscy testerzy i współtwórcy

---

**Stworzone z ❤️ dla społeczności Home Assistant**

📧 Problemy i pytania: [GitHub Issues](https://github.com/MuchaZ/smart-lights-control/issues) 