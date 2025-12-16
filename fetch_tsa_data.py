#!/usr/bin/env python3
"""
TSA Data Fetcher - Automatically fetch latest TSA checkpoint passenger data
Scrapes data from https://www.tsa.gov/travel/passenger-volumes
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup


class TSADataFetcher:
    """Fetch TSA checkpoint passenger data from official website."""
    
    BASE_URL = "https://www.tsa.gov/travel/passenger-volumes"
    
    def __init__(self, verbose=False):
        """Initialize fetcher with optional verbose output."""
        self.verbose = verbose
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def log(self, message):
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def fetch_year_data(self, year):
        """
        Fetch TSA data for a specific year.
        
        Args:
            year: Year to fetch (e.g., 2024)
            
        Returns:
            DataFrame with columns: date, passengers, year
        """
        url = f"{self.BASE_URL}/{year}"
        self.log(f"Fetching data for {year} from {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching data for {year}: {e}", file=sys.stderr)
            return None
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Find the data table
        # TSA uses a table with passenger data
        table = soup.find('table')
        if not table:
            print(f"Warning: No table found for {year}", file=sys.stderr)
            return None
        
        # Extract table data
        rows = []
        for tr in table.find_all('tr')[1:]:  # Skip header row
            cells = tr.find_all('td')
            if len(cells) >= 2:  # Need at least date and current year passengers
                date_str = cells[0].get_text(strip=True)
                passengers_str = cells[1].get_text(strip=True)
                
                # Clean up passenger count (remove commas, handle empty values)
                passengers_str = passengers_str.replace(',', '').strip()
                if not passengers_str or passengers_str == '-':
                    continue
                
                try:
                    # Parse date - TSA format is typically "MM/DD/YYYY"
                    date = pd.to_datetime(date_str)
                    passengers = int(passengers_str)
                    
                    rows.append({
                        'date': date,
                        'passengers': passengers,
                        'year': date.year
                    })
                except (ValueError, AttributeError) as e:
                    self.log(f"Skipping invalid row: {date_str}, {passengers_str} - {e}")
                    continue
        
        if not rows:
            print(f"Warning: No valid data extracted for {year}", file=sys.stderr)
            return None
        
        df = pd.DataFrame(rows)
        self.log(f"Successfully fetched {len(df)} records for {year}")
        return df
    
    def fetch_all_years(self, years):
        """
        Fetch data for multiple years and combine into single DataFrame.
        
        Args:
            years: List of years to fetch
            
        Returns:
            Combined DataFrame with all years' data
        """
        all_data = []
        
        for year in years:
            df = self.fetch_year_data(year)
            if df is not None and not df.empty:
                all_data.append(df)
        
        if not all_data:
            raise ValueError("No data was successfully fetched for any year")
        
        # Combine all years
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Sort by date
        combined_df = combined_df.sort_values('date').reset_index(drop=True)
        
        self.log(f"Total records fetched: {len(combined_df)}")
        self.log(f"Date range: {combined_df['date'].min()} to {combined_df['date'].max()}")
        
        return combined_df
    
    def save_to_csv(self, df, output_path):
        """
        Save DataFrame to CSV file.
        
        Args:
            df: DataFrame to save
            output_path: Path to output CSV file
        """
        # Ensure output directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        self.log(f"Data saved to {output_path}")
        print(f"✓ Successfully saved {len(df)} records to {output_path}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Fetch latest TSA checkpoint passenger data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch all years (2019-2025) and save to default location
  python fetch_tsa_data.py
  
  # Fetch specific years with verbose output
  python fetch_tsa_data.py --years 2023 2024 2025 --verbose
  
  # Save to custom location
  python fetch_tsa_data.py --output data/tsa_data.csv
        """
    )
    
    parser.add_argument(
        '--years',
        type=int,
        nargs='+',
        default=list(range(2019, 2026)),
        help='Years to fetch (default: 2019-2025)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='tsa_raw_data.csv',
        help='Output CSV file path (default: tsa_raw_data.csv)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed progress information'
    )
    
    args = parser.parse_args()
    
    # Print header
    print("=" * 70)
    print("TSA DATA FETCHER - Automated Data Download")
    print("=" * 70)
    print(f"Fetching years: {', '.join(map(str, args.years))}")
    print(f"Output file: {args.output}")
    print()
    
    try:
        # Create fetcher and fetch data
        fetcher = TSADataFetcher(verbose=args.verbose)
        df = fetcher.fetch_all_years(args.years)
        
        # Save to CSV
        fetcher.save_to_csv(df, args.output)
        
        # Print summary
        print()
        print("=" * 70)
        print("FETCH COMPLETE")
        print("=" * 70)
        print(f"Records: {len(df)}")
        print(f"Date range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
        print(f"Years: {sorted(df['year'].unique())}")
        print()
        print("You can now run the analysis:")
        print("  python tsa_holiday_analysis.py")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
