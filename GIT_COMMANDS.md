# 🚀 Komendy Git do wrzucenia projektu

## 📋 Przygotowanie repo

Wykonaj te komendy w folderze `/Users/barciemowicz/Downloads/lights-ha`:

### 1. Inicjalizacja Git
```bash
git init
```

### 2. Dodaj remote origin
```bash
git remote add origin git@github.com:MuchaZ/smart-lights-control.git
```

### 3. Sprawdź czy connection działa
```bash
ssh -T git@github.com
# Powinno pokazać: Hi MuchaZ! You've successfully authenticated...
```

### 4. Dodaj wszystkie pliki
```bash
git add .
```

### 5. Sprawdź status
```bash
git status
# Powinno pokazać wszystkie nowe pliki
```

### 6. Pierwszy commit
```bash
git commit -m "🧠 Initial release: Smart Lights Control with AI

✨ Features:
- Intelligent light control using linear regression
- Adaptive machine learning 
- Precise brightness calculations (±10lx accuracy)
- Automatic sample collection and outlier filtering
- Smart mode with fallback when regression quality low
- Full monitoring with sensors and switches
- Multi-room support via GUI configuration

🎯 Two installation methods:
- Custom Component (2min setup via HACS)
- Multi-file system (full control for advanced users)

📊 Includes:
- Custom HA component with config flow
- Python scripts for regression calculation
- Blueprints for automation
- Complete documentation and examples
- HACS compatibility"
```

### 7. Push do GitHuba
```bash
git branch -M main
git push -u origin main
```

## 🔍 Sprawdzenie po upload

1. **Idź do**: https://github.com/MuchaZ/smart-lights-control
2. **Sprawdź czy** wszystkie pliki się wgrały
3. **README.md** powinno wyświetlać się automatycznie
4. **Sprawdź badges** w README (mogą pokazywać 404 do pierwszego release)

## 📦 Przygotowanie do HACS

### 1. Utwórz pierwszy release
```
GitHub → Releases → Create a new release
Tag: v1.0.0
Title: 🧠 Smart Lights Control v1.0.0
Description: First release with AI-powered light control
```

### 2. Dodaj do HACS (opcjonalnie)
Po stworzeniu repo użytkownicy mogą dodać przez:
```
HACS → Integrations → Custom repositories
URL: https://github.com/MuchaZ/smart-lights-control
Category: Integration
```

## 🎉 Po publikacji

Twój projekt będzie dostępny na:
- **GitHub**: https://github.com/MuchaZ/smart-lights-control
- **Clone**: `git clone https://github.com/MuchaZ/smart-lights-control.git`
- **HACS**: Custom repository dla Home Assistant

## 📈 Następne kroki

1. **Przetestuj** instalację custom component
2. **Zbierz feedback** od użytkowników  
3. **Utwórz Issues** dla bugów i feature requests
4. **Rozważ PR** do oficjalnego HACS default repository

---

**Twój projekt AI dla Home Assistant jest gotowy do publikacji! 🚀** 