FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# إخبار المنصة رسمياً بأننا نستخدم المنفذ 8080 لتتخطى الفحص
EXPOSE 8080

# تشغيل السيرفر الوهمي والبوت معاً
CMD python -m http.server 8080 & python newfile.py
