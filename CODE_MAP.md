# CODE_MAP.md

## Healthcare Directory Collection Methods Reference

This document maps all collection methods available in the system, their implementation locations, usage instructions, and integration status.

---

## 📍 Collection Methods Overview

### 1. **Unified Pipeline Collection** ✅ INTEGRATED
**Location:** `scripts/run_pipeline.py` → `src/core/pipeline.py`  
**Status:** PRIMARY METHOD - Fully integrated  
**Description:** Main collection orchestrator that handles all phases (collect, process, publish)

**Usage:**
```bash
# Standard collection with keyword search
python3 scripts/run_pipeline.py --mode collect --limit 50

# Grid-based geographic collection (RECOMMENDED)
python3 scripts/run_pipeline.py --mode collect --use-grid --cities Tokyo,Nagoya --grid-size 3000 --limit 100

# Full pipeline (collect → process → publish)
python3 scripts/run_pipeline.py --mode full --limit 50
```

**Key Features:**
- Cost tracking and budget enforcement
- Progress tracking with database persistence
- Automatic deduplication
- English proficiency filtering
- Grid-based or keyword-based search

---

### 2. **Geographic Area Collection** ✅ INTEGRATED
**Location:** `add_geographic_providers.py`  
**Status:** Active - User-facing script  
**Description:** Collects providers by city/ward using the unified pipeline

**Usage:**
```bash
# Collect by city
python3 add_geographic_providers.py --city Tokyo --limit 50

# Collect by city and specific wards
python3 add_geographic_providers.py --city Tokyo --wards "Shibuya,Minato" --limit 100

# Collect with specific specialty
python3 add_geographic_providers.py --city Osaka --specialty "Dentistry" --limit 30
```

**Key Features:**
- Uses unified pipeline internally
- Supports ward-level targeting
- Specialty filtering
- Automatic English proficiency filtering

---

### 3. **Specific Provider Addition** ✅ INTEGRATED
**Location:** `add_specific_provider.py`  
**Status:** Active - User-facing script  
**Description:** Add individual providers by name or Google Place ID

**Usage:**
```bash
# Add by provider name and location
python3 add_specific_provider.py --name "St. Luke's International Hospital" --location "Tokyo"

# Add by Google Place ID
python3 add_specific_provider.py --place-id "ChIJN1t_tDeuEmsRUsoyG83frY4"

# Force update existing provider
python3 add_specific_provider.py --place-id "ChIJN1t_tDeuEmsRUsoyG83frY4" --force
```

**Key Features:**
- Bypasses English proficiency filter
- Can force update existing providers
- Direct database insertion

---

### 4. **Grid-Based Geographic Search** ✅ INTEGRATED
**Location:** `src/collectors/geographic_search.py`  
**Status:** Active - Core module  
**Description:** Divides geographic areas into grid squares for comprehensive coverage

**Usage (via pipeline):**
```bash
# Grid search through pipeline
python3 scripts/run_pipeline.py --mode collect --use-grid --cities Tokyo --grid-size 2000 --limit 500

# Multiple cities with grid
python3 scripts/run_pipeline.py --mode collect --use-grid --cities "Tokyo,Osaka,Kyoto" --grid-size 3000
```

**Key Features:**
- Prevents geographic clustering
- Adjustable grid size (meters)
- Multi-city support
- Comprehensive area coverage

---

### 5. **Direct Google Places Collector** ✅ CORE MODULE
**Location:** `src/collectors/google_places.py`  
**Status:** Core module - Used by all collection methods  
**Description:** Low-level Google Places API interface

**Key Methods:**
- `search_providers()` - Search only, doesn't save to database
- `collect_providers()` - Search, filter, and save to database
- `get_provider_details()` - Fetch detailed information
- `_calculate_proficiency_score()` - English proficiency scoring

**Direct Usage (not recommended for general use):**
```python
from src.collectors.google_places import GooglePlacesCollector

collector = GooglePlacesCollector()
# Collect and save to database
results = collector.collect_providers(
    search_query="dentist Tokyo",
    max_results=20
)
```

---

## ⚠️ DEPRECATED/ORPHANED Collection Methods

### 1. **collect_top_cities.py** ❌ DEPRECATED
**Location:** `scripts/collect_top_cities.py`  
**Status:** BROKEN - Do not use  
**Issue:** Uses `search_providers()` which doesn't save to database  
**Replacement:** Use `scripts/run_pipeline.py --mode collect --use-grid`

### 2. **Old Run Scripts** ❌ DEPRECATED
**Location:** `deprecated_scripts/` folder  
**Files:**
- `run_collection.py`
- `run_content_generation.py`
- `run_wordpress_sync.py`
- `run_full_pipeline.py`

**Status:** Replaced by unified `scripts/run_pipeline.py`  
**Do not use** - Moved to deprecated folder

---

## 🔄 Collection Workflow

### Standard Collection Flow:
```
1. User Input (script/command)
    ↓
2. Pipeline Runner (scripts/run_pipeline.py)
    ↓
3. Unified Pipeline (src/core/pipeline.py)
    ↓
4. Google Places Collector (src/collectors/google_places.py)
    ↓
5. Deduplication Check (src/collectors/deduplication.py)
    ↓
6. English Proficiency Filter (score ≥ 10)
    ↓
7. Database Storage (src/core/database.py)
```

### Collection Method Decision Tree:
```
Need to collect providers?
├── Multiple providers in area?
│   ├── Yes → Use grid search: run_pipeline.py --use-grid
│   └── No → Use keyword search: run_pipeline.py
├── Specific provider by name?
│   └── Use: add_specific_provider.py --name
└── Have Google Place ID?
    └── Use: add_specific_provider.py --place-id
```

---

## 📊 Collection Statistics

### Database Tables Used:
- `providers` - Main provider storage
- `processed_places` - Tracks evaluated Place IDs (SQLite cache)
- `pipeline_runs` - Pipeline execution history

### Cache Tables:
- `place_cache` - Google Places API response cache
- `processed_places` - Evaluated provider tracking

### Filtering Thresholds:
- **English Proficiency Minimum:** Score ≥ 10
- **Cache Duration:** 30 days for place details
- **Daily API Limit:** $25 (configurable)
- **Monthly API Limit:** $100 (configurable)

---

## 🚀 Quick Start Commands

### Most Common Collection Tasks:

```bash
# 1. Collect 100 providers in Tokyo using grid search
python3 scripts/run_pipeline.py --mode collect --use-grid --cities Tokyo --limit 100

# 2. Collect dental clinics in Osaka
python3 add_geographic_providers.py --city Osaka --specialty Dentistry --limit 50

# 3. Add specific hospital
python3 add_specific_provider.py --name "Keio University Hospital" --location Tokyo

# 4. Full pipeline for Kyoto (collect + AI content + publish)
python3 scripts/run_pipeline.py --mode full --use-grid --cities Kyoto --limit 50

# 5. Check collection status
python3 scripts/run_pipeline.py --status-only
```

---

## 🔍 Troubleshooting

### Common Issues:

**"Already processed" messages:**
- Provider was previously evaluated but rejected (low English score)
- Clear with: `python3 scripts/clear_location_data.py <location>`

**No providers collected:**
- Check English proficiency threshold
- Try different search keywords
- Use grid search for better coverage

**API limits reached:**
- Check: `python3 scripts/set_cost_limits.py --show`
- Adjust: `python3 scripts/set_cost_limits.py --daily 50 --monthly 200`

---

## 📝 Notes

- Always use `collect_providers()` method, not `search_providers()`
- Grid search is more comprehensive than keyword search
- The unified pipeline (`run_pipeline.py`) is the recommended method
- English proficiency score of 10+ is required for automatic collection
- Use `add_specific_provider.py` to bypass proficiency requirements

---

*Last Updated: 2025-01-26*