# Inteligentne Zarządzanie Światłem - Instrukcje

## Czym są poprawki?

Poprawiłem twoją regresję liniową w kilku kluczowych obszarach:

### 🔧 Główne poprawki:

1. **Spójność formatów danych** - teraz wszystko używa formatu `brightness:lux`
2. **Lepsza walidacja** - sprawdzamy czy dane są rozsądne (brightness 0-255, lux 0-10000)
3. **Filtrowanie outlierów** - automatyczne usuwanie nieprawidłowych próbek
4. **Jakość regresji** - obliczamy R² (współczynnik determinacji) i korelację
5. **Więcej próbek** - minimum 5 zamiast 2 punktów do regresji
6. **Lepsze logowanie** - szczegółowe informacje o jakości regresji
7. **Znaczniki czasu** - śledzenie kiedy zebrano próbki

## 📁 Pliki w systemie

- `calculate_brightness_regression.py` - oblicza regresję z zebranych danych
- `learn_brightness_lux.py` - zbiera próbki podczas działania systemu  
- `learn.yaml` - blueprint do automatycznego zbierania danych
- `lux_control.yaml` - sterowanie oświetleniem (niezmieniony)
- `configuration_example.yaml` - przykład konfiguracji HA

## 🚀 Instalacja

### 1. Skopiuj pliki Python
```bash
# W katalogu Home Assistant:
cp calculate_brightness_regression.py <config>/python_scripts/
cp learn_brightness_lux.py <config>/python_scripts/
```

### 2. Dodaj encje do configuration.yaml
Skopiuj odpowiednie sekcje z `configuration_example.yaml` do swojego `configuration.yaml`, zamieniając `garderoba_master` na nazwy swoich pokoi.

### 3. Restart Home Assistant

### 4. Utwórz automatyzacje
- Importuj blueprint `learn.yaml` 
- Skonfiguruj dla każdego pokoju osobno

## 📊 Jak interpretować wyniki

### Współczynnik R² (jakość regresji):
- **R² > 0.8** - 🟢 Bardzo dobra regresja
- **R² 0.5-0.8** - 🟡 Akceptowalna regresja  
- **R² < 0.5** - 🔴 Słaba regresja - sprawdź pozycjonowanie czujnika

### Przykładowe wartości:
```
Regresja: lux = 2.5 * brightness + 15
- a=2.5 (współczynnik kierunkowy)
- b=15 (lux przy brightness=0)
- R²=0.85 (bardzo dobra jakość)
```

## ⚙️ Najlepsze praktyki

### Pozycjonowanie czujnika lux:
1. **Umieść blisko lamp** - żeby mierzył rzeczywiste oświetlenie
2. **Unikaj bezpośredniego światła słońca** - może zaburzać pomiary
3. **Stabilna pozycja** - nie przesuwaj podczas zbierania danych

### Zbieranie danych:
1. **Różne jasności** - testuj od 10% do 100% brightness
2. **Różne pory dnia** - dzień/noc może wpływać na czujnik
3. **Stabilne warunki** - zamknij zasłony podczas testów
4. **Patience** - zbierz przynajmniej 20-30 próbek

### Troubleshooting:

#### Niska jakość regresji (R² < 0.5):
- Sprawdź czy czujnik lux reaguje na zmiany światła
- Może być za dużo światła naturalnego
- Czujnik może być wadliwy lub źle skalibrowany

#### Brak danych:
- Sprawdź logi Home Assistant (`Developer Tools > Logs`)
- Upewnij się że encje input_text istnieją
- Sprawdź czy automatyzacja jest włączona

#### Dziwne wartości współczynników:
- Ujemne `a` - może czujnik jest odwrócony lub światło nie wpływa na czujnik
- Bardzo duże `b` - może być dużo światła zewnętrznego
- `a` bliskie 0 - sprawdź czy czujnik w ogóle reaguje

## 🔍 Monitorowanie systemu

### Sensory do dodania na dashboard:
- `sensor.regression_quality_garderoba_master` - jakość regresji
- `sensor.predicted_lux_garderoba_master` - przewidywane lux
- `input_text.brightness_regression_garderoba_master` - pełne dane regresji

### Automatyzacje pomocnicze:
- Powiadomienia o niskiej jakości regresji
- Regularne przeliczanie regresji 
- Czyszczenie starych danych

## 📈 Rozwiązywanie problemów

### Jeśli regresja jest niestabilna:
1. Zbierz więcej danych (50+ próbek)
2. Sprawdź czy warunki są stabilne
3. Może być potrzeba 2 osobne regresje (dzień/noc)

### Jeśli światło nie reaguje poprawnie:
1. Sprawdź czy używasz najnowszej regresji
2. Może potrzeba innych trybów (nieliniowa regresja)
3. Sprawdź tolerancje w sterowniku (`deviation_margin`)

## 🧪 Testowanie

Dodaj to do `Developer Tools > Services`:
```yaml
service: python_script.calculate_brightness_regression
data:
  room_id: "garderoba_master"
```

Sprawdź wyniki w:
- `input_text.brightness_regression_garderoba_master`
- Logs w Home Assistant

## 💡 Przyszłe ulepszenia

Możesz rozważyć:
1. **Regresja wielomianowa** - dla nieliniowych zależności
2. **Uczenie maszynowe** - bardziej zaawansowane modele
3. **Kompensacja światła dziennego** - oddzielne modele dla różnych pór dnia
4. **Adaptacyjne learning** - system się dostosowuje w czasie 