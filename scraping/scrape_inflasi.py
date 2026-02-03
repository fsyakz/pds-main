#!/usr/bin/env python3
"""
Script untuk scraping data Inflasi dari Bank Indonesia
"""

import requests
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class InflasiScraper:
    """Scraper untuk data Inflasi"""
    
    def __init__(self):
        self.base_url = "https://www.bi.go.id"
        self.api_url = "https://www.bi.go.id/biweb/Templates/Web/eng/DataLanding.aspx"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def scrape_inflasi(self, year: int = None) -> Optional[pd.DataFrame]:
        """
        Scraping data inflasi tahunan
        
        Args:
            year: Tahun yang akan di-scrape, default tahun sekarang
            
        Returns:
            DataFrame dengan kolom ['Tanggal', 'Inflasi'] atau None jika gagal
        """
        try:
            if year is None:
                year = datetime.now().year
            
            # Payload untuk API request
            payload = {
                'node': '1245',  # Inflasi node ID
                'year': year,
                'format': 'json'
            }
            
            # Make request
            response = self.session.post(self.api_url, data=payload)
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            if not data or 'data' not in data:
                print("Tidak ada data ditemukan")
                return None
            
            # Convert to DataFrame
            records = []
            for item in data['data']:
                try:
                    # Asumsi format data inflasi per bulan
                    bulan = item['bulan']
                    tahun = item.get('tahun', year)
                    inflasi = float(item['nilai'].replace(',', '.'))
                    
                    # Konversi nama bulan ke angka
                    bulan_map = {
                        'Januari': 1, 'Februari': 2, 'Maret': 3, 'April': 4,
                        'Mei': 5, 'Juni': 6, 'Juli': 7, 'Agustus': 8,
                        'September': 9, 'Oktober': 10, 'November': 11, 'Desember': 12
                    }
                    
                    if bulan in bulan_map:
                        tanggal = datetime(tahun, bulan_map[bulan], 1)
                        records.append({
                            'Tanggal': tanggal,
                            'Inflasi': inflasi
                        })
                except (ValueError, KeyError) as e:
                    print(f"Error parsing record: {e}")
                    continue
            
            if not records:
                print("Tidak ada record valid yang berhasil diparse")
                return None
            
            df = pd.DataFrame(records)
            df = df.sort_values('Tanggal').reset_index(drop=True)
            
            return df
            
        except requests.RequestException as e:
            print(f"Error saat request ke API BI: {e}")
            return None
        except Exception as e:
            print(f"Error tidak terduga: {e}")
            return None
    
    def save_data(self, df: pd.DataFrame, year: int, output_dir: str = "data/scraping/inflasi") -> bool:
        """
        Menyimpan data ke file CSV dan Excel
        
        Args:
            df: DataFrame yang akan disimpan
            year: Tahun data
            output_dir: Directory output
            
        Returns:
            True jika berhasil, False jika gagal
        """
        try:
            # Create directory jika belum ada
            os.makedirs(output_dir, exist_ok=True)
            
            # Save to CSV
            csv_path = os.path.join(output_dir, f'inflasi_{year}.csv')
            df.to_csv(csv_path, index=False)
            print(f"Data disimpan ke: {csv_path}")
            
            # Save to Excel
            excel_path = os.path.join(output_dir, f'Inflasi_Tahunan_{year}.xlsx')
            df.to_excel(excel_path, index=False)
            print(f"Data disimpan ke: {excel_path}")
            
            # Save metadata
            metadata = {
                'last_updated': datetime.now().isoformat(),
                'year': year,
                'total_records': len(df),
                'date_range': {
                    'start': df['Tanggal'].min().isoformat(),
                    'end': df['Tanggal'].max().isoformat()
                },
                'source': 'Bank Indonesia API',
                'scraped_by': 'scrape_inflasi.py'
            }
            
            metadata_path = os.path.join(output_dir, f'metadata_{year}.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"Metadata disimpan ke: {metadata_path}")
            
            return True
            
        except Exception as e:
            print(f"Error menyimpan data: {e}")
            return False


def main():
    """Main function untuk menjalankan scraper"""
    print("=== Inflasi Scraper ===")
    
    scraper = InflasiScraper()
    current_year = datetime.now().year
    
    # Scrape data untuk tahun ini dan tahun lalu
    for year in [current_year, current_year - 1]:
        print(f"\nMengambil data inflasi tahun {year}...")
        df = scraper.scrape_inflasi(year=year)
        
        if df is None:
            print(f"Gagal mengambil data tahun {year}")
            continue
        
        print(f"Berhasil mengambil {len(df)} records")
        print(f"Rentang tanggal: {df['Tanggal'].min()} hingga {df['Tanggal'].max()}")
        print("\nSample data:")
        print(df.head())
        
        # Save data
        print(f"\nMenyimpan data tahun {year}...")
        if scraper.save_data(df, year):
            print(f"Data tahun {year} berhasil disimpan!")
        else:
            print(f"Gagal menyimpan data tahun {year}")


if __name__ == "__main__":
    main()
