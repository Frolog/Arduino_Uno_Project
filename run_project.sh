#!/bin/bash

echo "🚀 מתחיל תהליך הגדרה והרצה אוטומטי של הפרויקט..."

# 1. בדיקה והתקנה של חבילות מערכת חסרות (Apt)
echo "📦 בודק חבילות מערכת..."
MISSING_PACKAGES=()
dpkg -s python3-pip &>/dev/null || MISSING_PACKAGES+=("python3-pip")
dpkg -s python3-venv &>/dev/null || MISSING_PACKAGES+=("python3-venv")

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo "🔐 נדרשת סיסמת מנהל להתקנת החבילות: ${MISSING_PACKAGES[*]}"
    sudo apt update && sudo apt install -y "${MISSING_PACKAGES[@]}"
else
    echo "✅ כל חבילות המערכת מותקנות."
fi

# 2. זיהוי אוטומטי של חיבור ה-Arduino (החלפת מנגנון ה-COM)
echo "🔍 מחפש ארדואינו מחובר..."
ARDUINO_PORT=$(ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null | head -n 1)

if [ -z "$ARDUINO_PORT" ]; then
    echo "❌ שגיאה: לא נמצא ארדואינו מחובר! אנא חבר את ה-USB ונסה שוב."
    exit 1
fi
echo "✅ נמצא ארדואינו בפורט: $ARDUINO_PORT"

# 3. הגדרת הרשאות גישה (dialout) במידת הצורך
if ! groups $USER | grep &>/dev/null "\bdialout\b"; then
    echo "🔐 מוסיף הרשאות גישה לחומרה (dialout)..."
    sudo usermod -aG dialout $USER
    echo "⚠️ שים לב: נוספו הרשאות חדשות. מומלץ לבצע ריסטארט למחשב אם החיבור ייכשל."
fi

# 4. עדכון אוטומטי של הפורט בקובץ הפייתון
PYTHON_SCRIPT="Flask_console_web_graph_Arduino_auto_reconnect_with_cjmcu_v01.py"
if [ -f "$PYTHON_SCRIPT" ]; then
    echo "📝 מעדכן את הפורט בקוד הפייתון ל-$ARDUINO_PORT..."
    # מחליף את שורת ה-COM_PORT הנוכחית בפורט שנמצא אוטומטית
    sed -i "s|^COM_PORT = .*|COM_PORT = \"$ARDUINO_PORT\"|" "$PYTHON_SCRIPT"
else
    echo "❌ שגיאה: קובץ הפייתון $PYTHON_SCRIPT לא נמצא בתיקייה זו!"
    exit 1
fi

# 5. הגדרת הסביבה הוירטואלית והתקנת חבילות ה-Pip
if [ ! -d "venv" ]; then
    echo "📂 מייצר סביבה וירטואלית (venv)..."
    python3 -m venv venv
fi

echo "🔄 מפעיל סביבה וירטואלית ומעדכן חבילות..."
source venv/bin/activate

if [ -f "requirements.txt" ]; then
    pip install --default-timeout=100 -r requirements.txt
else
    echo "📦 קובץ requirements.txt חסר. מתקין חבילות בסיס באופן ידני..."
    pip install pyserial flask plotly
fi

# 6. שחרור הפורט במידה והוא תפוס ע"י תהליך אחר
echo "🧹 מנקה חיבורים ישנים על הפורט..."
sudo fuser -k "$ARDUINO_PORT" 2>/dev/null

# 7. הרצת השרת
echo "🎯 הכל מוכן! מפעיל את שרת הפייתון..."
echo "🌐 לאחר ההפעלה, היכנס בדפדפן לכתובת: http://127.0.0.1:5000"
python3 "$PYTHON_SCRIPT"
