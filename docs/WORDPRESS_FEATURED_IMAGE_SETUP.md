# WordPress Featured Image Block Setup Guide

## Overview
This guide explains how to set up the **Provider Featured Image Block** that displays Claude AI-selected featured images for healthcare providers.

## Files to Upload

### 1. Block Template File
**Upload to your WordPress theme directory:**

```
/wp-content/themes/your-theme-name/blocks/provider-featured-image.php
```

**File Location**: `blocks/provider-featured-image.php` (from this project)

### 2. ACF Field Configuration
**Add to your theme's functions.php or upload separately:**

**File Location**: `setup_acf_fields.php` (from this project)

The relevant sections are:
- Provider Featured Image Block registration
- Provider Featured Image Block field group

## WordPress Directory Structure

After upload, your WordPress theme should have:

```
/wp-content/themes/your-theme-name/
├── functions.php
├── blocks/
│   └── provider-featured-image.php    ← Upload this file
├── style.css
└── index.php
```

## Block Features

### 🎯 Smart Image Selection
- **Priority 1**: Claude AI-selected featured image (`external_featured_image` meta)
- **Priority 2**: First photo from `photo_urls` ACF field  
- **Priority 3**: WordPress native featured image
- **Fallback**: Professional healthcare placeholder

### 🛠️ Block Settings
Available in the WordPress block editor:

1. **Image Size**
   - Small (200px height)
   - Medium (300px height) 
   - Large (400px height)
   - Full (original aspect ratio)

2. **Caption Options**
   - Show/hide caption overlay
   - Custom caption text (HTML supported)

3. **AI Badge**
   - Show/hide "AI Selected" badge
   - Automatically appears for Claude-chosen images

4. **Alignment**
   - Normal, Wide, Full-width support

### 🎨 Styling Features
- **Responsive design** with mobile optimization
- **Hover effects** (subtle zoom on hover)
- **Professional styling** with shadows and rounded corners
- **AI badge** with modern glass-morphism effect
- **Placeholder graphics** for providers without images
- **Print-friendly** styles

## Implementation Steps

### Step 1: Upload Files
1. Upload `blocks/provider-featured-image.php` to `/wp-content/themes/your-theme/blocks/`
2. Ensure the file has proper permissions (644)

### Step 2: Update ACF Configuration  
1. Add the ACF field configuration from `setup_acf_fields.php`
2. Either include in functions.php or upload as separate ACF import
3. The block will automatically register when ACF is active

### Step 3: Verify Setup
1. Edit any healthcare provider post in WordPress
2. Click "+" to add a block
3. Look for "Provider Featured Image" in the Healthcare category
4. Add the block and configure settings

### Step 4: Test Display
1. Configure block settings (size, caption, etc.)
2. Save/preview the post
3. Verify image displays correctly
4. Check mobile responsiveness

## Image Sources & Priority

The block intelligently selects images in this order:

1. **Claude AI Selection** 🤖
   - Stored in `external_featured_image` meta field
   - Best photo chosen by Claude Vision API
   - Shows "AI Selected" badge

2. **First Available Photo** 📸
   - From `photo_urls` ACF field
   - Google Places photos
   - No AI selection badge

3. **WordPress Featured Image** 🖼️
   - Traditional WordPress featured image
   - Fallback option only

4. **Healthcare Placeholder** 🏥
   - Professional placeholder graphic
   - Provider name display
   - When no images available

## External URL Compliance

✅ **Google TOS Compliant**
- Uses direct photo URLs (no downloading)
- No media library storage required
- Maintains photo attribution to Google Places
- Respects Google's usage policies

## Block Customization

### CSS Customization
The block includes comprehensive built-in styles, but you can override with:

```css
/* Custom image size */
.provider-featured-image__img--custom {
    max-height: 350px;
    object-fit: cover;
}

/* Custom badge styling */
.provider-featured-image__badge {
    background: your-brand-color;
}

/* Custom placeholder */
.provider-featured-image__placeholder {
    background: your-custom-gradient;
}
```

### PHP Customization
You can modify the template file to:
- Add additional image sources
- Change fallback behavior  
- Customize placeholder content
- Add schema markup
- Integrate with other plugins

## Troubleshooting

### Block Not Appearing
- Verify ACF Pro is active
- Check file path: `/wp-content/themes/your-theme/blocks/provider-featured-image.php`
- Ensure functions.php includes the ACF configuration
- Clear any caching plugins

### Images Not Loading
- Check `external_featured_image` meta field exists
- Verify `photo_urls` ACF field has data
- Test image URLs directly in browser
- Check WordPress SSL settings for external images

### Styling Issues
- Clear browser cache
- Check theme conflicts
- Verify CSS is loading properly
- Test with default WordPress theme

## Integration with Healthcare Directory

This block is designed to work seamlessly with:
- **Claude AI Image Selection** system
- **Google Places Integration** for photo URLs
- **WordPress ACF Architecture** for provider data
- **External Featured Image** system (TOS compliant)

The block automatically detects and displays Claude AI-selected images when available, providing the best possible visual representation for each healthcare provider.

---

*This block template is part of the Healthcare Directory's advanced featured image system, leveraging Claude AI for intelligent image selection while maintaining full Google TOS compliance.* 