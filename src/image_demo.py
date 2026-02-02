import streamlit as st
import os
from pathlib import Path

def tampilkan_image_demo():
    """
    Demo berbagai cara menampilkan foto/gambar di Streamlit
    """
    st.title("Cara Menampilkan Foto di Web")
    
    # Cara 1: Menampilkan gambar dari file lokal
    st.subheader("1. Gambar dari File Lokal")
    st.markdown("Letakkan gambar di folder `assets/images/` atau folder lain dalam project")
    
    # Buat folder assets/images jika belum ada
    assets_dir = Path("assets/images")
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Contoh path gambar
    image_path = assets_dir / "contoh.jpg"
    
    if image_path.exists():
        st.image(str(image_path), caption="Contoh gambar dari file lokal", use_container_width=True)
    else:
        st.info(f"Gambar tidak ditemukan di: {image_path}")
        st.code("Letakkan gambar di folder assets/images/contoh.jpg")
    
    st.divider()
    
    # Cara 2: Upload gambar
    st.subheader("2. Upload Gambar")
    uploaded_file = st.file_uploader(
        "Pilih gambar untuk diupload",
        type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
        help="Support: PNG, JPG, JPEG, GIF, WebP"
    )
    
    if uploaded_file is not None:
        # Tampilkan gambar yang diupload
        st.image(uploaded_file, caption=f"Gambar: {uploaded_file.name}", use_container_width=True)
        
        # Tampilkan informasi file
        st.write("**Informasi File:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nama File", uploaded_file.name[:20] + "..." if len(uploaded_file.name) > 20 else uploaded_file.name)
        with col2:
            st.metric("Ukuran", f"{uploaded_file.size / 1024:.1f} KB")
        with col3:
            st.metric("Tipe", uploaded_file.type)
    
    st.divider()
    
    # Cara 3: Gambar dari URL
    st.subheader("3. Gambar dari URL")
    image_url = st.text_input(
        "Masukkan URL gambar:",
        placeholder="https://example.com/image.jpg",
        help="Masukkan URL lengkap ke gambar (http/https)"
    )
    
    if image_url:
        try:
            st.image(image_url, caption="Gambar dari URL", use_container_width=True)
        except Exception as e:
            st.error(f"Gagal memuat gambar: {e}")
    
    st.divider()
    
    # Cara 4: Multiple images gallery
    st.subheader("4. Galeri Gambar")
    
    # Upload multiple images
    uploaded_files = st.file_uploader(
        "Upload multiple gambar untuk galeri",
        type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
        accept_multiple_files=True,
        help="Pilih beberapa gambar sekaligus"
    )
    
    if uploaded_files:
        # Tampilkan dalam grid
        cols = st.columns(min(3, len(uploaded_files)))
        for i, img_file in enumerate(uploaded_files):
            with cols[i % 3]:
                st.image(img_file, caption=img_file.name, use_container_width=True)
    
    st.divider()
    
    # Cara 5: Background image dengan CSS
    st.subheader("5. Background Image")
    
    bg_image_url = st.text_input(
        "URL untuk background:",
        placeholder="https://example.com/background.jpg"
    )
    
    if bg_image_url:
        # Inject CSS untuk background
        st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("{bg_image_url}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .main .block-container {{
            background-color: rgba(255, 255, 255, 0.9);
            padding: 2rem;
            border-radius: 10px;
            margin: 1rem;
        }}
        </style>
        """, unsafe_allow_html=True)
        st.success("Background image applied!")
    
    st.divider()
    
    # Tips dan best practices
    st.subheader("Tips & Best Practices")
    
    with st.expander("Tips untuk gambar yang baik", expanded=False):
        st.markdown("""
        **Format Gambar:**
        - **PNG**: Best untuk gambar dengan teks, logo, transparansi
        - **JPG**: Best untuk foto, ukuran file lebih kecil
        - **WebP**: Modern format, kualitas bagus dengan ukuran kecil
        - **GIF**: Untuk animasi sederhana
        
        **Ukuran File:**
        - Optimal: < 500KB untuk web
        - Maksimal: < 2MB untuk performa baik
        - Compress gambar sebelum upload
        
        **Dimensi:**
        - Width: 800-1200px untuk display biasa
        - Height: 600-900px untuk landscape
        - Mobile: max-width 100%
        
        **Performance:**
        - Gunakan lazy loading untuk banyak gambar
        - Compress gambar dengan tools seperti TinyPNG
        - Gunakan CDN untuk production
        """)
    
    with st.expander("Code Examples", expanded=False):
        st.code("""
# Cara 1: Local file
st.image("path/to/image.jpg", caption="My Image")

# Cara 2: Upload file
uploaded_file = st.file_uploader("Choose image")
if uploaded_file:
    st.image(uploaded_file)

# Cara 3: URL
st.image("https://example.com/image.jpg")

# Cara 4: Multiple images
cols = st.columns(3)
for i, img in enumerate(images):
    with cols[i % 3]:
        st.image(img)

# Cara 5: Background CSS
st.markdown(f'''
<style>
.stApp {{
    background-image: url("{image_url}");
}}
</style>
''', unsafe_allow_html=True)
        """, language="python")

if __name__ == "__main__":
    tampilkan_image_demo()
