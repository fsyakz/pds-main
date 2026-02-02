# 🚀 Deploy ke Streamlit Cloud

Guide lengkap untuk deploy aplikasi PDS Dashboard ke Streamlit Cloud.

## 📋 Persyaratan

### 1. File yang Dibutuhkan
✅ `streamlit_app.py` - Entry point aplikasi  
✅ `requirements.txt` - Dependencies Python  
✅ `packages.txt` - System dependencies  
✅ Folder `supabase/` dengan data Excel  
✅ Folder `src/` dengan source code  

### 2. Struktur Folder
```
pds-main/
├── streamlit_app.py          # Main app file
├── requirements.txt          # Python dependencies
├── packages.txt              # System dependencies
├── setup.sh                  # Setup script
├── src/                      # Source code
├── supabase/                 # Data files
├── scraping/                 # Scraping data (optional)
└── DEPLOY.md                 # This file
```

## 🛠️ Cara Deploy

### Step 1: Prepare Repository
```bash
# Run setup script
./setup.sh

# Verify files exist
ls -la streamlit_app.py requirements.txt supabase/
```

### Step 2: Push to GitHub
```bash
git add .
git commit -m "Ready for Streamlit Cloud deployment"
git push origin main
```

### Step 3: Deploy ke Streamlit Cloud

1. **Login ke [Streamlit Cloud](https://share.streamlit.io/)**
2. **Klik "New app"**
3. **Connect repository:**
   - Pilih GitHub repository
   - Pilih branch `main`
   - Main file path: `streamlit_app.py`
4. **Advanced settings:**
   - Python version: `3.11` (recommended)
5. **Klik "Deploy"**

## 🔧 Konfigurasi Secrets

Setelah deploy, konfigurasi environment variables di Streamlit Cloud:

1. **Masuk ke dashboard Streamlit Cloud**
2. **Pilih aplikasi**
3. **Klik "Secrets"**
4. **Tambahkan secrets:**

```toml
SUPABASE_URL = "https://wqzqypljstedobmgsbuw.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_Gh4mup8y7i2ecibRQJOJIA_9yWDyycD"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndxenF5cGxqc3RlZG9ibWdzYnV3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODQ2NjYyOCwiZXhwIjoyMDg0MDQyNjI4fQ.MVvmLVx083em1PzJs7s6EYzdqrhizCUreWwvh9gHh3k"
SUPABASE_INFLASI_TABLE = "inflasi"
SUPABASE_BI_TABLE = "bi_7day_rr"
SUPABASE_JISDOR_TABLE = "kurs_jisdor"
SUPABASE_FETCH_LIMIT = "10000"
```

## 📊 Data Management

### Option 1: Upload Data Files
1. **Copy data Excel ke folder `supabase/`:**
   ```bash
   cp scraping/data/scraping/*/latest.xlsx supabase/
   ```

2. **Files yang dibutuhkan:**
   - `supabase/Inflasi_Tahunan_2024.xlsx`
   - `supabase/Inflasi_Tahunan_2025.xlsx`
   - `supabase/BI-7Day-RR.xlsx`
   - `supabase/Kurs_Jisdor.xlsx`

### Option 2: Use Supabase Database
1. **Setup Supabase project**
2. **Run SQL seed:**
   ```sql
   -- Jalankan file supabase/seed.sql
   -- atau supabase/seed_from_latest_data.sql
   ```

## 🐛 Troubleshooting

### Error: Module Not Found
**Problem:** `ModuleNotFoundError: No module named 'src'`

**Solution:** 
- Pastikan `streamlit_app.py` ada di root
- Check import path di file

### Error: File Not Found
**Problem:** Data Excel tidak ditemukan

**Solution:**
- Upload file ke folder `supabase/`
- Check file permissions
- Verify file names

### Error: Secrets Not Configured
**Problem:** Supabase connection failed

**Solution:**
- Konfigurasi secrets di Streamlit Cloud
- Check key names dan values

### Error: App Crashes on Load
**Problem:** Runtime error saat startup

**Solution:**
- Check logs di Streamlit Cloud
- Test locally dengan `streamlit run streamlit_app.py`
- Add error handling

## 🔄 Update Data

### Automatic Update
```bash
# Update dari scraping data
cd scraping
python3 update_data.py

# Push changes
git add .
git commit -m "Update data files"
git push origin main
```

### Manual Update
1. **Download data Excel baru**
2. **Replace files di `supabase/`**
3. **Push ke GitHub**

## 📱 Monitoring

### Check App Status
- **Streamlit Cloud dashboard** - Real-time logs
- **App URL** - Direct access
- **GitHub Actions** - CI/CD status

### Performance Tips
- **Cache data** dengan `@st.cache_data`
- **Limit data size** untuk loading cepat
- **Optimize images** dan assets

## 🔐 Security

### Best Practices
- **Use secrets** untuk API keys
- **Don't commit** sensitive data
- **Validate inputs** di semua forms
- **Rate limiting** untuk API calls

## 📞 Support

### Resources
- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [GitHub Issues](https://github.com/your-repo/issues)
- [Streamlit Community](https://discuss.streamlit.io/)

### Emergency Rollback
```bash
# Rollback ke previous commit
git revert HEAD
git push origin main
```

---

**🎉 Selamat meng-deploy!** 

Aplikasi akan tersedia di: `https://your-username-pds-main.streamlit.app/`
