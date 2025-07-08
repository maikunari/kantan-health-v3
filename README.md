# Healthcare Directory Automation

A comprehensive system for automatically collecting, processing, and publishing healthcare provider data for English-speaking patients in Japan.

## Overview

This automation system performs three main phases:
1. **Data Collection**: Searches Google Places API for healthcare providers
2. **AI Description Generation**: Creates natural, informative descriptions using Claude AI
3. **WordPress Publishing**: Publishes provider data to WordPress with proper categorization

## Search Process Explained

### How Search Queries Are Generated

The system generates search queries using:
- **Cities**: Tokyo, Yokohama, Osaka, Fukuoka, Kyoto (default)
- **Specialties**: 7 focused medical specialties from `specialties.json`
- **Search Terms**: 6 different English-friendly search patterns

**Query Formula:**
```
4 specialty-specific terms × 7 specialties × 5 cities = 140 queries
2 generic terms × 5 cities = 10 queries
Total = 150 search queries
```

**Example queries:**
- "English speaking Dentistry Tokyo"
- "International Emergency Medicine Osaka"
- "Foreign friendly Gynecology Fukuoka"
- "doctor Kyoto"

### Why You Get Fewer Results Than Queries

```
150 Search Queries → ~30-50 Unique Providers
```

**Key factors:**

1. **max_per_query Limitation**: Only takes top N results per query
   - `daily_limit < 50`: max_per_query = 1 (top result only)
   - `daily_limit ≥ 50`: max_per_query = 2 (top 2 results)

2. **Deduplication**: Same provider appears in multiple searches
   - "English speaking Dentistry Tokyo" and "International Dentistry Tokyo" 
   - Often return the same top dental clinic
   - System removes duplicates using `google_place_id`

3. **Cache Hits**: Previously searched queries return cached results

4. **Empty Results**: Some specific combinations return 0 providers

5. **Daily Limit**: Collection stops when reaching the daily provider limit

### max_per_query Calculation

| Daily Limit | max_per_query | Theoretical Max Results |
|-------------|---------------|------------------------|
| 5           | 1             | 150                    |
| 30          | 1             | 150                    |
| 50          | 2             | 300                    |
| 100         | 2             | 300                    |

## Command Line Usage

### Basic Usage
```bash
python3 run_automation.py --daily-limit 50
```

### All Available Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--daily-limit` | int | 25 | Daily limit for provider collection |
| `--max-per-query` | int | auto | Maximum results per search query |
| `--cities` | list | Tokyo Yokohama Osaka Fukuoka Kyoto | Cities to search |
| `--query-limit` | int | 200 | Maximum search queries to generate |
| `--batch-size` | int | 5 | Batch size for AI description generation |
| `--skip-collection` | flag | false | Skip data collection phase |
| `--skip-descriptions` | flag | false | Skip AI description generation |
| `--skip-publishing` | flag | false | Skip WordPress publishing |

### Example Commands

**High-volume collection:**
```bash
python3 run_automation.py --daily-limit 100 --max-per-query 3
```

**Specific cities:**
```bash
python3 run_automation.py --daily-limit 50 --cities Tokyo Osaka
```

**Only run descriptions (skip collection):**
```bash
python3 run_automation.py --skip-collection --skip-publishing
```

**Custom batch processing:**
```bash
python3 run_automation.py --daily-limit 75 --batch-size 10
```

**Test configuration:**
```bash
python3 run_automation.py --daily-limit 5 --cities Tokyo --query-limit 50
```

## Optimization Strategies

### For Maximum Provider Discovery

1. **Use higher daily limits:**
   ```bash
   python3 run_automation.py --daily-limit 100
   # Gets max_per_query=2, potential for 200+ unique providers
   ```

2. **Force higher max_per_query:**
   ```bash
   python3 run_automation.py --daily-limit 50 --max-per-query 5
   # Takes top 5 results from each query
   ```

3. **Clear cache for fresh results:**
   ```bash
   rm -rf cache/*.pkl
   python3 run_automation.py --daily-limit 50
   ```

### For Targeted Collection

1. **Focus on specific cities:**
   ```bash
   python3 run_automation.py --cities Tokyo Yokohama --daily-limit 30
   ```

2. **Generate more queries:**
   ```bash
   python3 run_automation.py --query-limit 300 --daily-limit 75
   ```

## File Structure

```
healthcare_directory_v2/
├── run_automation.py              # Main automation script
├── google_places_integration.py   # Google Places API integration
├── claude_description_generator.py # AI description generation
├── wordpress_integration.py       # WordPress publishing
├── medical_specialty_filter.py    # Specialty validation/normalization
├── specialties.json               # Current focused specialties (7)
├── specialties-full.json          # Complete specialty list (34)
├── cities.json                     # Japanese cities data
├── cache/                          # Cached Google Places results
└── config/                         # Environment configuration
```

## Configuration Files

### specialties.json (Current Focus)
```json
{
  "specialties": [
    "ENT (Ear, Nose & Throat)",
    "Dentistry", 
    "Emergency Medicine",
    "General Medicine",
    "Pharmacy",
    "Gynecology",
    "Internal Medicine"
  ]
}
```

### Environment Setup
Create `config/.env` with:
```
GOOGLE_API_KEY=your_google_places_api_key
ANTHROPIC_API_KEY=your_claude_api_key
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_HOST=localhost
WORDPRESS_URL=your_wordpress_site
WORDPRESS_USERNAME=your_wp_username
WORDPRESS_APP_PASSWORD=your_wp_app_password
```

## Cost Estimation

### Google Places API
- Text search: $0.017 per request
- Place details: $0.017 per request
- **Total per provider**: ~$0.034

### Claude AI
- Description generation: ~$0.01 per provider
- Batch processing reduces costs by ~40%

### Example Costs
| Daily Limit | Providers Found | Google API | Claude AI | Total |
|-------------|----------------|------------|-----------|-------|
| 30          | ~20            | $1.36      | $0.20     | $1.56 |
| 50          | ~35            | $2.38      | $0.35     | $2.73 |
| 100         | ~75            | $5.10      | $0.75     | $5.85 |

## Troubleshooting

### Low Results Despite High Daily Limit
- **Cause**: max_per_query too low, lots of duplicates
- **Solution**: Use `--max-per-query 3` or higher

### Cache Issues
- **Cause**: Loading old cached results
- **Solution**: Clear cache with `rm -rf cache/*.pkl`

### Specialty Formatting Issues
- **Cause**: Inconsistent specialty names
- **Solution**: System auto-normalizes to proper format (e.g., "ent" → "ENT (Ear, Nose & Throat)")

### API Rate Limits
- **Cause**: Too many requests too quickly
- **Solution**: Lower daily-limit or use built-in rate limiting

## Recent Improvements

### Fixed Issues
- ✅ **Phone numbers removed** from AI descriptions
- ✅ **Specialty formatting** standardized to proper display format
- ✅ **Description quality** improved with 140-150 word structured format
- ✅ **Batch processing** implemented for cost efficiency

### Enhanced Features
- ✅ **Flexible command line options** for different use cases
- ✅ **Smart deduplication** using multiple fingerprinting methods
- ✅ **Comprehensive logging** for debugging and monitoring
- ✅ **Phase skipping** for partial runs

## Support

For issues or questions:
1. Check the logs for specific error messages
2. Verify API keys in `config/.env`
3. Test with lower daily limits first
4. Clear cache if getting stale results 