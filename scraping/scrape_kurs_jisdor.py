#!/usr/bin/env python3
"""
Script untuk scraping data Kurs JISDOR dari Bank Indonesia
"""

import requests
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class KursScraper:
    """Scraper untuk data Kurs JISDOR"""
    
    def __init__(self):
        self.base_url = "https://www.bi.go.id"
        self.api_url = "https://www.bi.go.id/biweb/Templates/Web/eng/DataLanding.aspx"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def scrape_kurs_jisdor(self, days_back: int = 30) -> Optional[pd.DataFrame]:
        """
        Scraping data Kurs JISDOR untuk hari-hari terakhir
        
        Args:
            days_back: Jumlah hari ke belakang untuk di-scrape
            
        Returns:
            DataFrame dengan kolom ['Tanggal', 'Kurs'] atau None jika gagal
        """
        try:
            # Generate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Format dates untuk API BI
            start_date_str = start_date.strftime('%d/%m/%Y')
            end_date_str = end_date.strftime('%d/%m/%Y')
            
            # Payload untuk API request
            payload = {
                'node': '1244',  # Kurs JISDOR node ID
                'start': start_date_str,
                'end': end_date_str,
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
                    tanggal = datetime.strptime(item['tanggal'], '%d/%m/%Y')
                    kurs = float(item['nilai'].replace(',', '.'))
                    records.append({
                        'Tanggal': tanggal,
                        'Kurs': kurs
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
    
    def save_data(self, df: pd.DataFrame, output_dir: str = "data/scraping/kurs_jisdor") -> bool:
        """
        Menyimpan data ke file CSV dan Excel
        
        Args:
            df: DataFrame yang akan disimpan
            output_dir: Directory output
            
        Returns:
            True jika berhasil, False jika gagal
        """
        try:
            # Create directory jika belum ada
            os.makedirs(output_dir, exist_ok=True)
            
            # Save to CSV
            csv_path = os.path.join(output_dir, 'kurs_jisdor_latest.csv')
            df.to_csv(csv_path, index=False)
            print(f"Data disimpan ke: {csv_path}")
            
            # Save to Excel
            excel_path = os.path.join(output_dir, 'Kurs_Jisdor.xlsx')
            df.to_excel(excel_path, index=False)
            print(f"Data disimpan ke: {excel_path}")
            
            # Save metadata
            metadata = {
                'last_updated': datetime.now().isoformat(),
                'total_records': len(df),
                'date_range': {
                    'start': df['Tanggal'].min().isoformat(),
                    'end': df['Tanggal'].max().isoformat()
                },
                'source': 'Bank Indonesia API',
                'scraped_by': 'scrape_kurs_jisdor.py'
            }
            
            metadata_path = os.path.join(output_dir, 'metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"Metadata disimpan ke: {metadata_path}")
            
            return True
            
        except Exception as e:
            print(f"Error menyimpan data: {e}")
            return False


def main():
    """Main function untuk menjalankan scraper"""
    print("=== Kurs JISDOR Scraper ===")
    
    scraper = KursScraper()
    
    # Scrape data untuk 30 hari terakhir
    print("Mengambil data Kurs JISDOR...")
    df = scraper.scrape_kurs_jisdor(days_back=30)
    
    if df is None:
        print("Gagal mengambil data")
        return
    
    print(f"Berhasil mengambil {len(df)} records")
    print(f"Rentang tanggal: {df['Tanggal'].min()} hingga {df['Tanggal'].max()}")
    print("\nSample data:")
    print(df.head())
    
    # Save data
    print("\nMenyimpan data...")
    if scraper.save_data(df):
        print("Data berhasil disimpan!")
    else:
        print("Gagal menyimpan data")


if __name__ == "__main__":
    main()
