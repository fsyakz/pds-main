#!/bin/bash

# Setup script for Streamlit deployment
echo "🚀 Setting up PDS Dashboard for deployment..."

# Create necessary directories
mkdir -p supabase
mkdir -p data

# Copy sample data if not exists
if [ ! -f "supabase/Inflasi_Tahunan_2024.xlsx" ]; then
    echo "📊 Copying sample data files..."
    # Copy from scraping if available
    if [ -f "scraping/data/scraping/inflasi/Inflasi_Tahunan_2024.xlsx" ]; then
        cp scraping/data/scraping/inflasi/Inflasi_Tahunan_2024.xlsx supabase/
    fi
    if [ -f "scraping/data/scraping/inflasi/Inflasi_Tahunan_2025.xlsx" ]; then
        cp scraping/data/scraping/inflasi/Inflasi_Tahunan_2025.xlsx supabase/
    fi
    if [ -f "scraping/data/scraping/bi_7day_rr/BI-7Day-RR.xlsx" ]; then
        cp scraping/data/scraping/bi_7day_rr/BI-7Day-RR.xlsx supabase/
    fi
    if [ -f "scraping/data/scraping/kurs_jisdor/Kurs_Jisdor.xlsx" ]; then
        cp scraping/data/scraping/kurs_jisdor/Kurs_Jisdor.xlsx supabase/
    fi
fi

echo "✅ Setup completed!"
echo "📋 Next steps:"
echo "1. Deploy to Streamlit Cloud"
echo "2. Configure secrets in Streamlit Cloud dashboard"
