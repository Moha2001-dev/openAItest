# برنامج تتبع القطع الاستهلاكية وصيانات السيارة

برنامج سطر أوامر (CLI) بسيط يساعدك على:
- تسجيل القطع الاستهلاكية (مثل الزيت، الفلاتر، البواجي...).
- معرفة متى تصبح القطعة مستحقة للتغيير بناءً على عداد الكيلومترات.
- تسجيل كل عمليات الصيانة والاحتفاظ بسجل تاريخي.

## المتطلبات
- Python 3.9+

## التشغيل
```bash
python3 car_maintenance_tracker.py --help
```

## أمثلة استخدام

### 1) تحديث عداد السيارة الحالي
```bash
python3 car_maintenance_tracker.py set-mileage 128500
```

### 2) إضافة قطعة استهلاكية
> المثال التالي يضيف زيت المحرك كل 10000 كم وآخر تغيير عند 120000 كم.
```bash
python3 car_maintenance_tracker.py add-part "زيت المحرك" 10000 120000 --notes "5W-30"
```

### 3) تسجيل تغيير قطعة موجودة
```bash
python3 car_maintenance_tracker.py change-part "زيت المحرك" 129000 --notes "تغيير مع فلتر"
```

### 4) عرض القطع المستحقة
```bash
python3 car_maintenance_tracker.py due
```

### 5) تسجيل صيانة
```bash
python3 car_maintenance_tracker.py log-service "تغيير فلتر هواء" 129000 --cost 80 --details "فلتر أصلي"
```

### 6) عرض سجل الصيانات
```bash
python3 car_maintenance_tracker.py history
```

## ملف البيانات
يتم حفظ البيانات تلقائيًا في ملف:
- `car_maintenance_data.json`

ويمكن تغيير المسار باستخدام الخيار:
```bash
python3 car_maintenance_tracker.py --db my_data.json due
```
