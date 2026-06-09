@echo off
chcp 65001 > nul
echo 🚀 מתחיל תהליך הגדרה והרצה אוטומטי של הפרויקט עבור Windows...

:: 1. זיהוי אוטומטי של פורט ה-COM של הארדואינו
echo 🔍 מחפש ארדואינו מחובר...
set "ARDUINO_PORT="
for /f "tokens=2 delims=()" %%A in ('wmic path Win32_SerialPort get Caption 2^>nul ^| findstr /i "Arduino"') do (
    set "ARDUINO_PORT=%%A"
)

:: אם זיהוי ה-WMIC נכשל, ננסה דרך מנגנון ה-PNP
if "%ARDUINO_PORT%"=="" (
    for /f "tokens=2 delims=()" %%A in ('wmic pnpentity where "Name like '%%Arduino%%' and Caption like '%%COM%%'" get Caption 2^>nul') do (
        set "ARDUINO_PORT=%%A"
    )
)

if "%ARDUINO_PORT%"=="" (
    echo ❌ שגיאה: לא נמצא ארדואינו מחובר! אנא ודא שהדרייברים מותקנים והחבר את ה-USB.
    pause
    exit /b 1
)
echo ✅ נמצא ארדואינו בפורט: %ARDUINO_PORT%

:: 2. עדכון אוטומטי של הפורט בקוד הפייתון
set "PYTHON_SCRIPT=Flask_console_web_graph_Arduino_auto_reconnect_with_cjmcu_v01.py"
echo 📝 מעדכן את הפורט בקוד הפייתון ל-%ARDUINO_PORT%...
powershell -Command "(Get-Content %PYTHON_SCRIPT%) -replace '^COM_PORT = .*', 'COM_PORT = \"%ARDUINO_PORT%\"' | Set-Content %PYTHON_SCRIPT%"

:: 3. הגדרת הסביבה הוירטואלית והתקנת חבילות בפייתון
if not exist "venv" (
    echo 📂 מייצר סביבה וירטואלית (venv)...
    python -m venv venv
)

echo 🔄 מפעיל סביבה וירטואלית ומעדכן חבילות...
call venv\Scripts\activate

if exist "requirements.txt" (
    pip install --default-timeout=100 -r requirements.txt
) else (
    echo 📦 קובץ requirements.txt חסר. מתקין חבילות בסיס באופן ידני...
    pip install pyserial flask plotly
)

:: 4. הרצת השרת
echo 🎯 הכל מוכן! מפעיל את שרת הפייתון...
echo 🌐 לאחר ההפעלה, היכנס בדפדפן לכתובת: http://127.0.0.1:5000
python "%PYTHON_SCRIPT%"
pause
