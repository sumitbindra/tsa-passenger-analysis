#!/usr/bin/env python3
"""
TSA Passenger Data Analysis - Holiday-Aligned Weekly Averages
Aligns TSA checkpoint passenger data by US travel holidays rather than calendar weeks.
"""

import pandas as pd
import numpy as np
import yaml
from datetime import datetime, timedelta
from dateutil.easter import easter
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

class HolidayWeekCalculator:
    """Calculate holiday-aligned weeks for TSA data."""
    
    def __init__(self, config_path='holiday_config.yaml'):
        """Initialize with configuration file."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.holiday_weeks = self.config['holiday_weeks']
    
    def get_nth_weekday(self, year, month, n, weekday):
        """
        Get the nth occurrence of a weekday in a given month.
        weekday: 0=Monday, 1=Tuesday, ..., 6=Sunday
        """
        first_day = datetime(year, month, 1)
        first_weekday = first_day.weekday()
        
        # Calculate days until first occurrence of target weekday
        days_ahead = (weekday - first_weekday) % 7
        first_occurrence = first_day + timedelta(days=days_ahead)
        
        # Get nth occurrence
        target_date = first_occurrence + timedelta(weeks=n-1)
        return target_date
    
    def get_last_weekday(self, year, month, weekday):
        """Get the last occurrence of a weekday in a given month."""
        # Get first day of next month
        if month == 12:
            first_next_month = datetime(year + 1, 1, 1)
        else:
            first_next_month = datetime(year, month + 1, 1)
        
        # Go back to last day of current month
        last_day = first_next_month - timedelta(days=1)
        
        # Find last occurrence of weekday
        days_back = (last_day.weekday() - weekday) % 7
        return last_day - timedelta(days=days_back)
    
    def get_anchor_date(self, year, holiday_week):
        """Calculate the actual anchor date for a holiday in a given year."""
        anchor_type = holiday_week.get('anchor_type', 'fixed')
        
        if anchor_type == 'fixed':
            month, day = map(int, holiday_week['anchor_date'].split('-'))
            return datetime(year, month, day)
        
        elif anchor_type == 'relative':
            rule = holiday_week.get('relative_rule')
            
            if rule == 'third_monday_january':
                return self.get_nth_weekday(year, 1, 3, 0)
            elif rule == 'third_monday_february':
                return self.get_nth_weekday(year, 2, 3, 0)
            elif rule == 'easter':
                return easter(year)
            elif rule == 'last_monday_may':
                return self.get_last_weekday(year, 5, 0)
            elif rule == 'first_monday_september':
                return self.get_nth_weekday(year, 9, 1, 0)
            elif rule == 'second_monday_october':
                return self.get_nth_weekday(year, 10, 2, 0)
            elif rule == 'fourth_thursday_november':
                return self.get_nth_weekday(year, 11, 4, 3)
    
    def get_week_bounds(self, anchor_date, week_offset=0):
        """
        Get Monday-Sunday bounds for a week given an anchor date.
        Returns (monday, sunday) as datetime objects.
        """
        # Apply week offset
        anchor_date = anchor_date + timedelta(weeks=week_offset)
        
        # Find Monday of this week
        days_since_monday = anchor_date.weekday()
        monday = anchor_date - timedelta(days=days_since_monday)
        
        # Sunday is 6 days after Monday
        sunday = monday + timedelta(days=6)
        
        return monday, sunday
    
    def get_all_holiday_weeks(self, year):
        """Get all holiday weeks for a given year."""
        weeks = []
        
        for holiday_week in self.holiday_weeks:
            anchor_date = self.get_anchor_date(year, holiday_week)
            if anchor_date is None:
                continue
            
            week_offset = holiday_week.get('week_offset', 0)
            monday, sunday = self.get_week_bounds(anchor_date, week_offset)
            
            weeks.append({
                'name': holiday_week['name'],
                'year': year,
                'monday': monday,
                'sunday': sunday,
                'priority': holiday_week.get('priority', 0),
                'spans_year_boundary': holiday_week.get('spans_year_boundary', False)
            })
        
        return weeks


class TSADataProcessor:
    """Process TSA data and align by holiday weeks."""
    
    def __init__(self, data_path='tsa_raw_data.csv', config_path='holiday_config.yaml'):
        """Initialize with data and configuration."""
        self.df = pd.read_csv(data_path)
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.calculator = HolidayWeekCalculator(config_path)
        self.config = self.calculator.config
    
    def assign_holiday_week(self, row):
        """Assign a holiday week to a data row."""
        date = row['date']
        # Convert pandas Timestamp to date object
        if hasattr(date, 'date'):
            date_dt = date.date()
        else:
            date_dt = date
        year = date.year
        
        # Get all holiday weeks for this year
        weeks = self.calculator.get_all_holiday_weeks(year)
        
        # Find which week this date falls into
        for week in weeks:
            monday_date = week['monday'].date() if hasattr(week['monday'], 'date') else week['monday']
            sunday_date = week['sunday'].date() if hasattr(week['sunday'], 'date') else week['sunday']
            if monday_date <= date_dt <= sunday_date:
                return week['name']
        
        # If date falls in a holiday week that spans year boundary
        if date.month == 12:
            weeks_next = self.calculator.get_all_holiday_weeks(year + 1)
            for week in weeks_next:
                if week['spans_year_boundary']:
                    monday_date = week['monday'].date() if hasattr(week['monday'], 'date') else week['monday']
                    sunday_date = week['sunday'].date() if hasattr(week['sunday'], 'date') else week['sunday']
                    if monday_date <= date_dt <= sunday_date:
                        return week['name']
        elif date.month == 1:
            weeks_prev = self.calculator.get_all_holiday_weeks(year - 1)
            for week in weeks_prev:
                if week['spans_year_boundary']:
                    monday_date = week['monday'].date() if hasattr(week['monday'], 'date') else week['monday']
                    sunday_date = week['sunday'].date() if hasattr(week['sunday'], 'date') else week['sunday']
                    if monday_date <= date_dt <= sunday_date:
                        return week['name']
        
        return None
    
    def process_data(self):
        """Process data and assign holiday weeks."""
        self.df['holiday_week'] = self.df.apply(self.assign_holiday_week, axis=1)
        
        # Remove rows not assigned to any holiday week
        self.df_holiday = self.df[self.df['holiday_week'].notna()].copy()
        
        # Calculate weekly averages by holiday week and year
        self.weekly_avg = self.df_holiday.groupby(['holiday_week', 'year']).agg({
            'passengers': ['mean', 'sum', 'count'],
            'date': ['min', 'max']
        }).reset_index()
        
        self.weekly_avg.columns = ['holiday_week', 'year', 'avg_passengers', 
                                    'total_passengers', 'day_count', 'week_start', 'week_end']
        
        return self.weekly_avg
    
    def save_enhanced_data(self, output_path='tsa_enhanced_data.csv'):
        """Save enhanced data with holiday week assignments."""
        self.df.to_csv(output_path, index=False)
        print(f"Enhanced data saved to {output_path}")
    
    def save_weekly_averages(self, output_path='tsa_weekly_averages.csv'):
        """Save calculated weekly averages."""
        self.weekly_avg.to_csv(output_path, index=False)
        print(f"Weekly averages saved to {output_path}")


class TSAVisualizer:
    """Create visualizations of TSA data."""
    
    def __init__(self, weekly_avg_df, raw_df, config_path='holiday_config.yaml'):
        """Initialize with weekly averages data."""
        self.df = weekly_avg_df
        self.raw_df = raw_df
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        self.config = config['visualization']
        
        # Define distinct colors for each year
        self.year_colors = {
            2019: '#1f77b4',  # Blue
            2020: '#ff7f0e',  # Orange
            2021: '#2ca02c',  # Green
            2022: '#d62728',  # Red
            2023: '#9467bd',  # Purple
            2024: '#8c564b',  # Brown
            2025: '#e377c2'   # Pink
        }
    
    def plot_holiday_aligned_weeks(self, output_path='tsa_holiday_aligned_plot.png'):
        """Create plot with separate lines for each year, each with distinct color, in strict chronological order."""
        
        # Define strict chronological order of holidays (by date in year)
        holiday_order = [
            'New Year Holiday',
            'MLK Jr. Day',
            'Presidents Day',
            'Spring Break',
            'Easter/Spring Holiday',
            'Memorial Day',
            'July 4th Independence Day',
            'Labor Day',
            'Columbus Day',
            'Halloween',
            'Veterans Day',
            'Thanksgiving',
            'Black Friday',
            'Christmas Holiday'
        ]
        
        # Create figure
        fig, ax = plt.subplots(figsize=self.config['figure_size'])
        
        # Plot each year as a separate line with distinct color
        years = sorted(self.df['year'].unique())
        
        for year in years:
            year_data = self.df[self.df['year'] == year].copy()
            
            # Filter to only holidays that exist in chronological order
            year_data_ordered = []
            for holiday in holiday_order:
                holiday_rows = year_data[year_data['holiday_week'] == holiday]
                if len(holiday_rows) > 0:
                    year_data_ordered.append(holiday_rows.iloc[0])
            
            if len(year_data_ordered) == 0:
                continue
            
            year_data_ordered = pd.DataFrame(year_data_ordered)
            
            # Create x-axis positions
            x_positions = range(len(year_data_ordered))
            
            # Use distinct color for each year
            color = self.year_colors.get(int(year), '#000000')
            ax.plot(x_positions, year_data_ordered['avg_passengers'], 
                   marker='o', linewidth=self.config['line_width'],
                   markersize=self.config['marker_size'],
                   label=str(year), color=color)
        
        # Formatting
        ax.set_xlabel(self.config['xlabel'], fontsize=12, fontweight='bold')
        ax.set_ylabel(self.config['ylabel'], fontsize=12, fontweight='bold')
        ax.set_title(self.config['title'], fontsize=14, fontweight='bold')
        ax.grid(self.config['grid'], alpha=0.3)
        ax.legend(loc=self.config['legend_loc'], fontsize=10)
        
        # Set x-axis labels to holiday week names (only those that exist)
        existing_holidays = [h for h in holiday_order if h in self.df['holiday_week'].unique()]
        ax.set_xticks(range(len(existing_holidays)))
        ax.set_xticklabels(existing_holidays, rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=self.config['dpi'], bbox_inches='tight')
        print(f"Plot saved to {output_path}")
        plt.close()
    
    def plot_pivot_heatmap(self, output_path='tsa_heatmap.png'):
        """Create a heatmap showing passenger volumes across years and holidays, sorted chronologically."""
        
        # Create pivot table
        pivot_df = self.df.pivot_table(values='avg_passengers', 
                                       index='holiday_week', 
                                       columns='year')
        
        # Define chronological order of holidays (by approximate date in year)
        holiday_order = [
            'New Year Holiday',
            'MLK Jr. Day',
            'Presidents Day',
            'Spring Break',
            'Easter/Spring Holiday',
            'Memorial Day',
            'July 4th Independence Day',
            'Labor Day',
            'Columbus Day',
            'Halloween',
            'Veterans Day',
            'Thanksgiving',
            'Black Friday',
            'Christmas Holiday'
        ]
        
        # Reorder rows by chronological order
        pivot_df = pivot_df.reindex([h for h in holiday_order if h in pivot_df.index])
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 10))
        
        sns.heatmap(pivot_df, annot=True, fmt='.0f', cmap='YlOrRd', 
                   ax=ax, cbar_kws={'label': 'Average Daily Passengers'})
        
        ax.set_title('TSA Average Daily Passengers by Holiday Week and Year (Chronological Order)', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Year', fontsize=12, fontweight='bold')
        ax.set_ylabel('Holiday Week', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=self.config['dpi'], bbox_inches='tight')
        print(f"Heatmap saved to {output_path}")
        plt.close()
    
    def plot_calendar_weeks_with_holidays(self, output_path='tsa_calendar_weeks_plot.png'):
        """Create plot with 52 calendar weeks on x-axis, showing holiday points only."""
        
        # Create figure with subplots for each year
        years = sorted(self.raw_df['year'].unique())
        fig, axes = plt.subplots(len(years), 1, figsize=(16, 3*len(years)), sharex=True)
        
        if len(years) == 1:
            axes = [axes]
        
        for idx, year in enumerate(years):
            ax = axes[idx]
            year_data = self.raw_df[self.raw_df['year'] == year].copy()
            
            # Calculate ISO week number for each date
            year_data['iso_week'] = year_data['date'].dt.isocalendar().week
            
            # Get holiday weeks for this year
            holiday_week_data = self.df[self.df['year'] == year].copy()
            
            # Create scatter plot for holidays only
            for _, holiday_row in holiday_week_data.iterrows():
                holiday_name = holiday_row['holiday_week']
                avg_passengers = holiday_row['avg_passengers']
                
                # Get the ISO week of the week_start date
                week_start = pd.Timestamp(holiday_row['week_start'])
                iso_week = week_start.isocalendar()[1]
                
                color = self.year_colors.get(year, '#000000')
                ax.scatter(iso_week, avg_passengers, s=200, color=color, 
                          marker='o', edgecolors='black', linewidth=1.5, zorder=3)
                
                # Add holiday name as tooltip-like text
                ax.annotate(holiday_name, xy=(iso_week, avg_passengers),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=8, alpha=0.7)
            
            # Formatting
            ax.set_ylabel(f'{year}\\nAvg Daily Passengers', fontsize=11, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            ax.set_ylim(0, self.raw_df['passengers'].max() * 1.1)
        
        # Set x-axis for calendar weeks
        axes[-1].set_xlabel('ISO Calendar Week Number', fontsize=12, fontweight='bold')
        axes[-1].set_xticks(range(1, 54, 2))
        
        fig.suptitle('TSA Passenger Volumes - Calendar Weeks with Holiday Markers (2019-2025)', 
                    fontsize=14, fontweight='bold', y=0.995)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=self.config['dpi'], bbox_inches='tight')
        print(f"Calendar weeks plot saved to {output_path}")
        plt.close()


def main():
    """Main execution function."""
    
    print("=" * 70)
    print("TSA PASSENGER DATA - HOLIDAY-ALIGNED ANALYSIS (UPDATED)")
    print("=" * 70)
    
    # Process data
    print("\n1. Processing TSA data...")
    processor = TSADataProcessor('tsa_raw_data.csv', 'holiday_config.yaml')
    processor.process_data()
    
    print(f"   - Total records: {len(processor.df)}")
    print(f"   - Records assigned to holiday weeks: {len(processor.df_holiday)}")
    print(f"   - Holiday weeks identified: {processor.df_holiday['holiday_week'].nunique()}")
    
    # Save enhanced data
    print("\n2. Saving enhanced data...")
    processor.save_enhanced_data('tsa_enhanced_data.csv')
    processor.save_weekly_averages('tsa_weekly_averages.csv')
    
    # Create visualizations
    print("\n3. Creating visualizations...")
    visualizer = TSAVisualizer(processor.weekly_avg, processor.df, 'holiday_config.yaml')
    visualizer.plot_holiday_aligned_weeks('tsa_holiday_aligned_plot.png')
    visualizer.plot_pivot_heatmap('tsa_heatmap.png')
    visualizer.plot_calendar_weeks_with_holidays('tsa_calendar_weeks_plot.png')
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print("\nGenerated files:")
    print("  - tsa_enhanced_data.csv (raw data with holiday week assignments)")
    print("  - tsa_weekly_averages.csv (calculated weekly averages)")
    print("  - tsa_holiday_aligned_plot.png (line plot by year - UPDATED with distinct colors)")
    print("  - tsa_heatmap.png (heatmap visualization - UPDATED chronological order)")
    print("  - tsa_calendar_weeks_plot.png (NEW: 52-week calendar with holiday points)")
    print("  - holiday_config.yaml (configuration file - edit to customize)")


if __name__ == '__main__':
    main()
