# Black Git Iran

همگام‌سازی پروژه بین چند نفر — بدون API، با **Rubika Web** به‌عنوان سرور (وقتی اینترنت هست).

## نصب

```bash
pip install -r requirements.txt
playwright install chromium
```

## اجرا

```bash
python main.py
```

## نحوه کار

1. **تنظیمات** → لینک گروه/کانال روبیکا، مسیر پروژه، پوشه موقت
2. **ارسال نسخه جدید** → پروژه ZIP می‌شود (فایل‌های اصلی دست نمی‌خورند) و در گروه آپلود می‌شود
3. **دریافت نسخه جدید** → با نام نسخه، ZIP از گروه دانلود → استخراج در مسیر موقت → بکاپ → جایگزینی اتمیک → پاک‌سازی موقت

### جریان دریافت (ایمن در برابر خرابی وسط کار)

```
Rubika → download → upload-one-time/
       → extract (موقت) → verify → backup → atomic replace
       → پاک‌سازی upload-one-time/
```

### فایل‌ها

- `.black-sync.json` — داخل هر زیپ: نام پروژه، نسخه، تاریخ، تعداد فایل، هش SHA-256 هر فایل
- `.blackgitignore` — الگوهای حذف از زیپ (مثل `.gitignore`)

## نکته‌ها

- **ورود به روبیکا:** بار اول پنجره مرورگر باز می‌شود؛ وارد شوید. سشن در پوشه `browser-profile` ذخیره می‌شود و دفعات بعد نیازی به ورود نیست. پسورد جایی ذخیره نمی‌شود.
- **سلکتورها:** روبیکا DOM خود را عوض می‌کند. اگر دانلود/آپلود شکست خورد، اسکرین‌شات `debug-*.png` در پوشه پروفایل مرورگر ذخیره می‌شود و سلکتورهای `SEL_*` در `blackgit/transport/rubika/web.py` را به‌روز کنید.
- **بکاپ‌ها:** قبل از جایگزینی، نسخه فعلی در `%APPDATA%\BlackGitIran\backups` کپی می‌شود.

## معماری (آماده برای افزودن LAN)

```
blackgit/
├── core/           # zip, hash, metadata, ignore, atomic-replace
├── transport/      # رابط Transport
│   └── rubika/     # پیاده‌سازی Playwright (بدون API)
└── ui/             # tkinter ویندوزی
```

بعداً `transport/lan.py` با همان رابط `Transport` اضافه می‌شود — بدون تغییر هسته.
