#!/usr/bin/env python3
"""
Main script untuk menjalankan semua scraper
"""

import os
import sys
from datetime import datetime

# Add current directory to path untuk import scrapers
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrape_bi_7day_rr import BIScraper
from scrape_kurs_jisdor import KursScraper
from scrape_inflasi import InflasiScraper


def main():
    """Main function untuk menjalankan semua scraper"""
    print("=== Running All Scrapers ===")
    print(f"Timestamp: {datetime.now()}")
    print("=" * 50)
    
    # Base output directory
    base_output_dir = "data/scraping"
    
    # 1. Scrape BI-7Day-RR
    print("\n1. Scraping BI-7Day-RR...")
    bi_scraper = BIScraper()
    bi_df = bi_scraper.scrape_bi_7day_rr(days_back=30)
    
    if bi_df is not None:
        if bi_scraper.save_data(bi_df, os.path.join(base_output_dir, "bi_7day_rr")):
            print("✓ BI-7Day-RR scraping berhasil")
        else:
            print("✗ BI-7Day-RR scraping gagal menyimpan")
    else:
        print("✗ BI-7Day-RR scraping gagal")
    
    # 2. Scrape Kurs JISDOR
    print("\n2. Scraping Kurs JISDOR...")
    kurs_scraper = KursScraper()
    kurs_df = kurs_scraper.scrape_kurs_jisdor(days_back=30)
    
    if kurs_df is not None:
        if kurs_scraper.save_data(kurs_df, os.path.join(base_output_dir, "kurs_jisdor")):
            print("✓ Kurs JISDOR scraping berhasil")
        else:
            print("✗ Kurs JISDOR scraping gagal menyimpan")
    else:
        print("✗ Kurs JISDOR scraping gagal")
    
    # 3. Scrape Inflasi
    print("\n3. Scraping Inflasi...")
    inflasi_scraper = InflasiScraper()
    current_year = datetime.now().year
    
    success_count = 0
    for year in [current_year, current_year - 1]:
        inflasi_df = inflasi_scraper.scrape_inflasi(year=year)
        
        if inflasi_df is not None:
            if inflasi_scraper.save_data(inflasi_df, year, os.path.join(base_output_dir, "inflasi")):
                print(f"✓ Inflasi {year} scraping berhasil")
                success_count += 1
            else:
                print(f"✗ Inflasi {year} scraping gagal menyimpan")
        else:
            print(f"✗ Inflasi {year} scraping gagal")
    
    # Summary
    print("\n" + "=" * 50)
    print("Scraping Summary:")
    print(f"- BI-7Day-RR: {'✓' if bi_df is not None else '✗'}")
    print(f"- Kurs JISDOR: {'✓' if kurs_df is not None else '✗'}")
    print(f"- Inflasi: {'✓' if success_count > 0 else '✗'} ({success_count}/2 tahun)")
    print(f"Completed at: {datetime.now()}")


if __name__ == "__main__":
    main()
