# 🧠 Smart Lights Control

**Inteligentny system zarządzania oświetleniem używający regresji liniowej i adaptacyjnego uczenia maszynowego.**

## ✨ Główne zalety

- ⚡ **Natychmiastowe reakcje** - 1 precyzyjna korekta zamiast 3-5 prób na ślepo
- 🎯 **Wysoka dokładność** - ±10lx zamiast ±50lx tolerancji  
- 🧠 **Samodoskonalenie** - system uczy się z każdą zmianą światła
- 📊 **Pełny monitoring** - sensory jakości regresji i statusu smart mode
- 🛡️ **Zabezpieczenia** - automatyczny fallback gdy regresja niedokładna

## 🎯 Jak to działa

Zamiast ślepego zmieniania jasności o stały krok (+20, +20, +20...), system:

1. **Zbiera dane** - pary brightness→lux automatycznie
2. **Oblicza regresję** - równanie lux = a × brightness + b  
3. **Przewiduje precyzyjnie** - brightness = (target_lux - b) / a
4. **Uczy się adaptacyjnie** - poprawia model na bieżąco

## 🚀 Przed i Po

### PRZED:
```
Potrzebuję 300lx
❌ Ustaw 100 brightness... 250lx (za mało)
❌ Dodaj +20... 280lx (wciąż za mało)  
❌ Dodaj +20... 320lx (za dużo, ale trudno)
```

### PO:
```
Potrzebuję 300lx
🧠 Regresja: lux = 2.5 × brightness + 15
✅ Ustaw (300-15)/2.5 = 114 brightness = dokładnie 300lx!
```

## 📦 Co dostajesz

Po instalacji automatycznie dostajesz dla każdego pokoju:

### Sensory
- **Regression Quality** - Jakość regresji (R²)
- **Sample Count** - Liczba próbek  
- **Smart Mode Status** - Status (Smart/Fallback/Learning)
- **Predicted Lux** - Przewidywane lux
- **Average Error** - Błąd przewidywań

### Przełączniki  
- **Smart Mode** - Włącz/wyłącz inteligentne sterowanie
- **Adaptive Learning** - Włącz/wyłącz adaptacyjne uczenie

### Serwisy
- **calculate_regression** - Przelicz model regresji
- **clear_samples** - Wyczyść zebrane próbki
- **add_sample** - Dodaj próbkę ręcznie
- **adaptive_learning** - Uruchom adaptacyjne uczenie

## ⚡ Instalacja i konfiguracja

1. **Zainstaluj przez HACS**
2. **Restart Home Assistant**  
3. **Dodaj integrację**: Settings → Integrations → Smart Lux Control
4. **Wypełnij formularz**: pokój, lampa, czujnik lux, czujnik ruchu
5. **Gotowe!** System zacznie zbierać dane automatycznie

## 🏠 Multi-room support

Każdy pokój = osobna integracja z własnymi:
- Sensorami monitoringu
- Modelem regresji  
- Ustawieniami

Dodaj kolejny pokój przez: Add Integration → Smart Lux Control

## 📈 Monitorowanie

Obserwuj jakość regresji (R²):
- **R² > 0.8** 🟢 - Doskonała, smart mode w pełni aktywny
- **R² 0.5-0.8** 🟡 - Dobra, system działa prawidłowo
- **R² < 0.5** 🔴 - Słaba, automatyczny tryb awaryjny

---

**Twoje światło będzie naprawdę inteligentne! 🧠💡** 