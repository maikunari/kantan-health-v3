# AI Content Generation Summary

## Overview
The healthcare directory uses **Claude AI (Anthropic)** to automatically generate professional content for healthcare providers. All content is generated using real provider data and optimized for both user experience and search engine optimization.

## AI-Generated Content Types

### 6 Content Types Generated Per Provider:

1. **AI Description** (150-175 words)
   - Two-paragraph professional description
   - Medical services and English language support
   - Patient experience and practical information

2. **AI Excerpt** (50-75 words)
   - Concise summary for listings and previews
   - Key strengths and location highlights

3. **Review Summary** (80-100 words)
   - Patient feedback analysis
   - Consistent praise points from reviews

4. **English Experience Summary** (80-100 words)
   - English language support details
   - International patient communication experience

5. **SEO Title** (50-60 characters)
   - Search engine optimized titles
   - Format: "[Specialty] in [Location] | [Provider Name]"

6. **SEO Meta Description** (150-160 characters)
   - Click-optimized descriptions for search results
   - Includes location, specialty, and call-to-action

## Data Sources & Parameters

### Provider Information Used:
- **Provider Name & Location**: City, district, prefecture (with Tokyo ward special handling)
- **Medical Specialties**: Primary and secondary specialties
- **English Proficiency**: Rated levels (Native, High, Intermediate, Good, Basic, Unknown)
- **Rating & Reviews**: Google Places rating and review count
- **Review Content**: Actual patient reviews for insights
- **Accessibility**: Wheelchair accessibility and parking availability
- **Business Hours**: Operating schedule information
- **Contact Details**: Phone, website, address

### Location Intelligence:
- **Tokyo Ward Formatting**: "Tokyo, Shibuya" instead of "Shibuya, Tokyo"
- **Geographic Context**: District, city, prefecture hierarchy
- **Local SEO Targeting**: City and district-specific keywords

### Quality Indicators:
- **Rating Thresholds**: 4.0+ stars with 10+ reviews highlighted
- **English Support Levels**: Differentiated language support descriptions
- **Review Insights**: Extracted patient experience themes

## Technical Implementation

### AI Model:
- **Model**: Claude 3.5 Sonnet (Anthropic)
- **Processing**: Mega-batch system (6 content types in 1 API call)
- **Token Allocation**: 3,000 tokens per provider for premium quality
- **Temperature**: 0.6 for descriptions, 0.3 for SEO content

### Efficiency:
- **Batch Size**: 4 providers per API call
- **API Reduction**: 96% fewer calls than individual generation
- **Processing Speed**: 4x faster than individual content generation

### Quality Control:
- **Length Validation**: Automatic character/word count enforcement
- **Fallback Content**: Generated if AI processing fails
- **Consistency**: Standardized formatting across all providers

## Content Integration

### WordPress Integration:
- **Yoast SEO**: Automatic title and meta description population
- **ACF Fields**: All content stored in Advanced Custom Fields
- **Post Creation**: Automated WordPress post generation

### Database Storage:
- **Content Hashing**: Change detection for updates
- **Status Tracking**: Generation and publication status
- **Version Control**: Content update history

## Result Quality

The AI system generates **professional, location-specific, and medically accurate content** that:
- Helps patients find appropriate healthcare providers
- Improves search engine rankings through local SEO
- Provides consistent, high-quality information across all providers
- Scales efficiently for large healthcare directories

All content is generated from real provider data and actual patient reviews, ensuring authenticity and relevance for healthcare seekers. 