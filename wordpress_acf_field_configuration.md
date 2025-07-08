# WordPress ACF Field Configuration for Healthcare Directory

This document outlines the required ACF (Advanced Custom Fields) configuration for the healthcare directory integration.

## Field Groups and Fields

### Provider Details Field Group
- **provider_phone**: Text Field
- **wheelchair_accessible**: Select Field
  - Choices:
    - `accessible` : Wheelchair Accessible
    - `not_accessible` : Not Wheelchair Accessible  
    - `unknown` : Accessibility Unknown
- **parking_available**: Select Field
  - Choices:
    - `available` : Parking Available
    - `not_available` : Parking Not Available
    - `unknown` : Parking Unknown
- **business_status**: Text Field
- **prefecture**: Text Field

### Business Hours Field Group
- **business_hours**: Textarea Field (for complete formatted hours)
- **hours_monday**: Text Field
- **hours_tuesday**: Text Field
- **hours_wednesday**: Text Field
- **hours_thursday**: Text Field
- **hours_friday**: Text Field
- **hours_saturday**: Text Field
- **hours_sunday**: Text Field
- **open_now**: Select Field
  - Choices:
    - `Open Now` : Currently Open
    - `Closed` : Currently Closed
    - `Status unknown` : Status Unknown

### Location & Navigation Field Group
- **latitude**: Number Field
- **longitude**: Number Field
- **nearest_station**: Text Field
- **google_maps_embed**: Textarea Field

### Language Support Field Group
- **english_proficiency**: Select Field
  - Choices:
    - `Fluent` : Fluent English
    - `Conversational` : Conversational English
    - `Basic` : Basic English
    - `Unknown` : English Level Unknown
- **proficiency_score**: Number Field
- **english_indicators**: Textarea Field

### Photo Gallery Field Group
- **photo_urls**: Textarea Field

### Accessibility & Services Field Group
- **accessibility_status**: Select Field (same choices as wheelchair_accessible)
- **parking_status**: Select Field (same choices as parking_available)

### Patient Insights Field Group
- **review_keywords**: Textarea Field
- **patient_highlights**: Textarea Field

### Additional Essential Fields
- **provider_website**: URL Field
- **provider_address**: Textarea Field
- **provider_rating**: Text Field
- **provider_reviews**: Text Field
- **postal_code**: Text Field
- **ai_description**: Textarea Field
- **provider_city**: Text Field

## Important Notes

1. **Field Names**: Use the exact field names as specified above
2. **Select Field Values**: Use the exact values as specified for select fields
3. **Field Types**: Match the field types exactly as specified
4. **Required Fields**: Consider making essential fields like provider_phone, provider_address required
5. **Business Hours**: The individual day fields (hours_monday, etc.) will contain formatted time ranges like "9:00 AM - 5:00 PM" or "Closed"

## Business Hours Format Examples

The business_hours field will contain formatted text like:
```
Monday: 9:00 AM – 5:00 PM
Tuesday: 9:00 AM – 5:00 PM
Wednesday: 9:00 AM – 5:00 PM
Thursday: 9:00 AM – 5:00 PM
Friday: 9:00 AM – 5:00 PM
Saturday: 9:00 AM – 1:00 PM
Sunday: Closed
```

Individual day fields will contain:
- `9:00 AM - 5:00 PM` for open days
- `Closed` for closed days  
- `Hours not available` when data is missing 