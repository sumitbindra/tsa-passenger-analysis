# TSA Passenger Data Analysis - Holiday-Aligned Weekly Averages

## Overview

This project analyzes TSA checkpoint passenger data from 2019-2025, aligning weekly averages by **US travel holidays** rather than calendar weeks. This approach reveals true seasonal patterns in passenger traffic driven by major travel events.

## Key Innovation

Instead of traditional week-of-year analysis, this system:
- **Identifies anchor dates** for each major US travel holiday (Thanksgiving, Christmas, Independence Day, etc.)
- **Calculates Monday-Sunday weeks** centered on these holidays
- **Compares the same holiday weeks across years** to reveal patterns and trends
- **Handles year-boundary holidays** (e.g., Christmas spanning Dec 25 - Jan 2)

## Data Source

- **TSA Official Checkpoint Travel Numbers**: https://www.tsa.gov/travel/passenger-volumes
- **Automated Fetching**: Use `fetch_tsa_data.py` to download latest data automatically
- **Time Period**: January 1, 2019 - Present
- **Update Frequency**: TSA updates data Monday-Friday by 9 AM
- **Coverage**: 14 major holiday travel periods

## Files Generated

### Data Files
- **`tsa_raw_data.csv`** - Raw daily passenger data downloaded from TSA
- **`tsa_enhanced_data.csv`** - Raw data with holiday week assignments
- **`tsa_weekly_averages.csv`** - Calculated weekly averages by holiday and year

### Configuration
- **`holiday_config.yaml`** - Holiday definitions and visualization settings (editable)

### Visualizations
- **`tsa_holiday_aligned_plot.png`** - Line plot with 7 distinct colored lines (one per year), showing passenger volumes across holiday periods
- **`tsa_heatmap.png`** - Heatmap arranged chronologically by holiday date, showing passenger volumes across years
- **`tsa_calendar_weeks_plot.png`** - NEW: 52 ISO calendar weeks on x-axis with colored points showing only where holidays occur each year

### Scripts
- **`fetch_tsa_data.py`** - Automated data fetcher (downloads latest TSA data)
- **`tsa_holiday_analysis.py`** - Main analysis script (executable)

## Holiday Weeks Analyzed

1. **New Year Holiday** - Week containing January 1
2. **MLK Jr. Day** - Week containing third Monday in January
3. **Presidents Day** - Week containing third Monday in February
4. **Spring Break** - Approximate week of March 20
5. **Easter/Spring Holiday** - Week containing Easter (varies by year)
6. **Memorial Day** - Week containing last Monday in May
7. **July 4th Independence Day** - Week containing July 4
8. **Labor Day** - Week containing first Monday in September
9. **Columbus Day** - Week containing second Monday in October
10. **Halloween** - Week containing October 31
11. **Veterans Day** - Week containing November 11
12. **Thanksgiving** - Week containing fourth Thursday in November
13. **Black Friday** - Week after Thanksgiving
14. **Christmas Holiday** - Week containing December 25

## Visualizations Explained

### 1. Holiday-Aligned Line Plot
- **X-axis**: Holiday travel periods (chronologically ordered)
- **Y-axis**: Average daily passengers (in millions)
- **Lines**: Each year (2019-2025) in distinct colors:
  - 2019: Blue
  - 2020: Orange
  - 2021: Green
  - 2022: Red
  - 2023: Purple
  - 2024: Brown
  - 2025: Pink
- **Insight**: Clearly shows pandemic impact (2020 orange line) and recovery trajectory

### 2. Chronological Heatmap
- **Rows**: Holiday weeks (ordered by when they occur in the year)
- **Columns**: Years (2019-2025)
- **Colors**: Yellow (low volumes) to Dark Red (high volumes)
- **Insight**: Shows seasonal patterns and year-over-year trends at a glance

### 3. Calendar Weeks Plot (NEW)
- **X-axis**: ISO calendar week numbers (1-53)
- **Y-axis**: Average daily passengers
- **Points**: Only appear when a holiday occurs in that week for that year
- **Colors**: Each year has distinct color
- **Labels**: Holiday names annotated on each point
- **Insight**: Shows which calendar weeks contain holidays and how volumes vary by year

## Key Findings

### Pandemic Impact (2020)
- Dramatic 50-60% drop in passenger volumes across all holiday weeks
- Lowest point: Easter/Spring Holiday 2020 (128K avg daily passengers)
- Recovery began in 2021

### Recovery Trajectory (2021-2024)
- Steady recovery from 2021 through 2024
- 2024 shows highest volumes in most holiday weeks
- Thanksgiving and Christmas remain peak travel periods

### Busiest Holiday Weeks (2024)
1. **Memorial Day**: 2.63M avg daily passengers
2. **July 4th Independence Day**: 2.62M
3. **Columbus Day**: 2.61M
4. **Christmas Holiday**: 2.57M
5. **Spring Break**: 2.54M

### Lowest Traffic Periods
- **MLK Jr. Day**: Generally 1.75M avg
- **Presidents Day**: Generally 2.07M avg
- **Labor Day**: Generally 1.95M avg

## How to Use

### Fetch Latest TSA Data

To download the most recent TSA checkpoint passenger data:

```bash
# Using uv (recommended)
uv run fetch_tsa_data.py --verbose

# Or using Python directly
python fetch_tsa_data.py --verbose
```

This will:
- Automatically scrape data from the TSA website for years 2019-2025
- Save to `tsa_raw_data.csv` in the correct format
- Show progress information with `--verbose` flag

**Options:**
```bash
# Fetch specific years only
uv run fetch_tsa_data.py --years 2023 2024 2025

# Save to custom location
uv run fetch_tsa_data.py --output data/my_tsa_data.csv

# See all options
uv run fetch_tsa_data.py --help
```

**Note:** Data is updated by TSA Monday-Friday by 9 AM. Run this script periodically to keep your analysis current.

### Run the Analysis
```bash
python3 tsa_holiday_analysis.py
```

This will:
1. Load raw TSA data
2. Assign each day to its corresponding holiday week
3. Calculate weekly averages
4. Generate all three visualizations
5. Save enhanced datasets

### Customize Configuration

Edit `holiday_config.yaml` to:
- Adjust holiday definitions
- Change visualization colors
- Modify figure size and styling
- Add new holiday weeks
- Change data processing settings

### Analyze the Data

Open the CSV files in your preferred tool:
- **Excel/Sheets**: For pivot tables and custom analysis
- **Python/Pandas**: For programmatic analysis
- **Tableau/Power BI**: For interactive dashboards

## Data Quality Notes

- **2025 Data**: Incomplete (through December 4, 2025)
- **Holiday Week Assignment**: 656 of 2,530 records (26%) assigned to holiday weeks
- **Unassigned Records**: Days outside defined holiday weeks
- **Year Boundary**: Christmas Holiday weeks may span Dec 25 - Jan 2

## Technical Details

### Holiday Calculation Rules
- **Fixed Dates**: New Year (Jan 1), Independence Day (Jul 4), Veterans Day (Nov 11), Christmas (Dec 25)
- **Relative Dates**: MLK Day (3rd Monday Jan), Presidents Day (3rd Monday Feb), Memorial Day (last Monday May), Labor Day (1st Monday Sep), Columbus Day (2nd Monday Oct), Thanksgiving (4th Thursday Nov)
- **Variable Dates**: Easter (calculated using dateutil.easter)

### Week Alignment
- All weeks start on **Monday** and end on **Sunday**
- 7 consecutive days per week
- Year boundary weeks handled by checking previous/next year's holiday definitions

### Averaging Method
- **Daily Average**: Sum of all passengers in week / number of days in week
- Handles partial weeks (e.g., 2025 data only has 4 days for some holidays)

### Calendar Week Mapping
- Uses ISO 8601 week numbering (weeks 1-53)
- Week 1 contains January 4th
- Allows comparison across years on same calendar weeks

## Dependencies

- Python 3.8+
- pandas
- numpy
- matplotlib
- seaborn
- pyyaml
- python-dateutil
- beautifulsoup4 (for data fetching)
- requests (for data fetching)
- lxml (for HTML parsing)

## Interpretation Guide

### Reading the Line Plot
- **Pandemic Signature**: 2020 (orange) shows dramatic dip across all holidays
- **Recovery Pattern**: Green (2021) and red (2022) show steady recovery
- **Current State**: Brown (2024) and pink (2025) show near-normal or elevated volumes
- **Seasonal Peaks**: Notice which holidays consistently have highest volumes

### Reading the Heatmap
- **Yellow cells**: Pandemic-impacted periods (2020)
- **Dark red cells**: Peak travel periods
- **Chronological flow**: Top to bottom shows progression through the year
- **Year comparison**: Left to right shows evolution over time

### Reading the Calendar Weeks Plot
- **Point density**: Shows which calendar weeks are busiest across years
- **Vertical spread**: Shows variation in passenger volumes for same holiday across years
- **Color patterns**: Each year's color shows its unique trajectory
- **Holiday clustering**: Shows how holidays cluster in certain weeks (e.g., late November/December)

## Future Enhancements

Potential additions to this analysis:
- Forecast passenger volumes for 2026+
- Compare against airline capacity data
- Analyze airport-specific patterns
- Incorporate weather and economic indicators
- Build predictive models for staffing optimization
- Add day-of-week analysis within holiday weeks

## Contact & Questions

For questions about this analysis or to suggest improvements, refer to the configuration file for customization options.

---

**Last Updated**: December 7, 2025  
**Data Through**: December 4, 2025  
**Analysis Period**: 2019-2025  
**Visualizations**: 3 (line plot, heatmap, calendar weeks)
