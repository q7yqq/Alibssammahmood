FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# أمر تشغيل البوت مع سيرفر ويب وهمي في نفس الوقت لمنع المنصة من إغلاقه
CMD python -m http.server 8080 & python newfile.py
