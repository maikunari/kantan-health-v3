# English Proficiency Ranking System

## Overview

The Healthcare Directory uses a sophisticated **English Proficiency Ranking System** to help international patients find healthcare providers who can communicate effectively in English. This system analyzes multiple data sources and uses Natural Language Processing (NLP) to generate accurate proficiency scores.

## Scoring Scale

Our system uses a **1-5 scale** that's easy to understand:

| Score | Level | Description |
|-------|-------|-------------|
| **5** | **Fluent** | Strong evidence of English-speaking staff and excellent communication |
| **4** | **Conversational** | Good English support with clear communication capabilities |
| **3** | **Basic** | Limited English support but some communication possible |
| **0** | **Unknown** | No evidence of English language support |

## Data Sources Analyzed

### 1. **Google Reviews** (Primary Source)
- Patient reviews mentioning English communication
- Sentiment analysis of English-related comments
- Volume of English mentions across multiple reviews

### 2. **Business Website**
- Presence of English version (/en/ URL structure)
- English language indicators in website content

### 3. **Business Name**
- International keywords (International, English, Foreign, Expat, Global)
- Multilingual service indicators

## Detailed Scoring Algorithm

### Review Text Analysis

The system searches for specific English-related phrases and assigns weighted scores:

#### **High-Value Indicators** (20 points positive / 10 points negative)
- "English speaking staff"
- "Speaks English well"
- "English communication confirmed"

#### **Medium-Value Indicators** (15 points positive / 8 points negative)
- "Translator available"
- "Translation services"
- "Interpreter provided"

#### **Basic Indicators** (10 points positive / 5 points negative)
- "Basic English"
- "Limited English"
- "Some English support"

#### **General Mentions** (5 points)
- Any mention of "English", "bilingual", "international"

### Sentiment Analysis

Each English mention is analyzed for sentiment:
- **Positive sentiment** → Higher point values
- **Negative sentiment** → Lower point values
- Uses TextBlob sentiment analysis library

### Volume Weighting

Multiple mentions increase confidence:
- **5+ English mentions** → +10 bonus points
- **1+ English mentions** → +5 bonus points

### Website Analysis

- **English website version** (/en/ in URL) → +10 points

### Business Name Analysis

- **International keywords** in name → +5 points

## Conversion to Final Scale

Internal scores (0-100) are converted to the 1-5 scale:

```
40+ points  → Fluent (5/5)
20-39 points → Conversational (4/5)  
10-19 points → Basic (3/5)
0-9 points   → Unknown (0/5)
```

## Examples

### Example 1: Fluent (5/5)
**Tokyo International Clinic**
- Multiple reviews: "English speaking staff confirmed, excellent bilingual service"
- Website has /en/ version
- "International" in business name
- **Total: 50 points → Fluent (5/5)**

### Example 2: Conversational (4/5)
**Osaka Medical Center**
- Reviews mention: "Translator service available"
- Some English support noted
- **Total: 25 points → Conversational (4/5)**

### Example 3: Basic (3/5)
**Local Clinic Shibuya**
- Reviews: "Limited English but staff tries"
- Basic communication possible
- **Total: 20 points → Basic (3/5)**

### Example 4: Unknown (0/5)
**Neighborhood Clinic**
- Reviews: "Great service but no English"
- No English support evidence
- **Total: 10 points → Unknown (0/5)**

## Technical Implementation

### Primary Calculation
Located in: `google_places_integration.py`
Method: `analyze_english_proficiency()`

### Data Storage
- Database field: `proficiency_score` (0-5 integer)
- Database field: `english_proficiency` (text: Fluent/Conversational/Basic/Unknown)

### WordPress Integration
- Uses stored scores directly (no recalculation)
- ACF field: `proficiency_score` with 0-5 validation
- Single source of truth maintained

## Benefits

✅ **Evidence-Based**: Scores based on actual patient reviews and concrete data
✅ **Sentiment-Aware**: Distinguishes between positive and negative English mentions  
✅ **Multi-Source**: Analyzes reviews, website, and business information
✅ **Weighted Scoring**: More reliable evidence gets higher weight
✅ **Volume Confidence**: Multiple mentions increase scoring confidence
✅ **Consistent Scale**: Simple 1-5 rating system throughout platform

## Maintenance

- **Single Algorithm**: Only one scoring system to maintain and improve
- **No Conflicts**: WordPress integration uses Google Places scores directly
- **Scalable**: Can easily add new data sources or adjust weights
- **Debuggable**: Clear scoring breakdown for each provider

## Future Enhancements

Potential improvements to consider:
- Integration with official medical translation services
- Analysis of appointment booking systems for English support
- Machine learning model training on patient feedback
- Integration with government healthcare language support databases 