<?php
/**
 * Provider Featured Image Block Template
 * 
 * Displays the Claude-selected featured image for healthcare providers
 * Uses external URLs (Google Places photos) without media library storage
 * 
 * @package Healthcare Directory
 * @version 1.0
 */

// Create id attribute allowing for custom "anchor" value.
$id = 'provider-featured-image-' . $block['id'];
if( !empty($block['anchor']) ) {
    $id = $block['anchor'];
}

// Create class attribute allowing for custom "className" and "align" values.
$className = 'provider-featured-image';
if( !empty($block['className']) ) {
    $className .= ' ' . $block['className'];
}
if( !empty($block['align']) ) {
    $className .= ' align' . $block['align'];
}

// Get the featured image URL (Claude-selected or fallback)
$featured_image_url = '';

// Method 1: Try to get Claude-selected featured image from external_featured_image meta
$external_featured_image = get_post_meta(get_the_ID(), 'external_featured_image', true);
if ($external_featured_image) {
    $featured_image_url = $external_featured_image;
}

// Method 2: Fallback to first photo from photo_urls ACF field
if (empty($featured_image_url)) {
    $photo_urls = get_field('photo_urls');
    if ($photo_urls) {
        // Handle both newline-separated and JSON formats
        if (is_string($photo_urls)) {
            $photo_array = explode("\n", trim($photo_urls));
            if (count($photo_array) == 1 && strpos($photo_urls, '[') === 0) {
                // Might be JSON format
                $json_decoded = json_decode($photo_urls, true);
                if (is_array($json_decoded)) {
                    $photo_array = $json_decoded;
                }
            }
        } else {
            $photo_array = is_array($photo_urls) ? $photo_urls : [];
        }
        
        if (!empty($photo_array) && !empty($photo_array[0])) {
            $featured_image_url = trim($photo_array[0]);
        }
    }
}

// Method 3: Final fallback to WordPress featured image
if (empty($featured_image_url) && has_post_thumbnail()) {
    $featured_image_url = get_the_post_thumbnail_url(get_the_ID(), 'large');
}

// Get additional field options for display customization
$image_size = get_field('image_size') ?: 'large';
$show_caption = get_field('show_caption') ?: false;
$image_caption = get_field('image_caption') ?: '';
$show_ai_badge = get_field('show_ai_badge') !== false ? get_field('show_ai_badge') : true;

// Get provider name for alt text
$provider_name = get_field('provider_name') ?: get_the_title();
?>

<div id="<?php echo esc_attr($id); ?>" class="<?php echo esc_attr($className); ?>">
    <?php if ($featured_image_url): ?>
        
        <div class="provider-featured-image__container">
            <img 
                src="<?php echo esc_url($featured_image_url); ?>" 
                alt="<?php echo esc_attr($provider_name . ' - Healthcare Facility'); ?>"
                class="provider-featured-image__img provider-featured-image__img--<?php echo esc_attr($image_size); ?>"
                loading="lazy"
                decoding="async"
            />
            
            <?php if ($show_caption && $image_caption): ?>
                <div class="provider-featured-image__caption">
                    <?php echo wp_kses_post($image_caption); ?>
                </div>
            <?php endif; ?>
            
            <!-- Claude AI Selection Badge (optional) -->
            <?php if ($external_featured_image && $show_ai_badge): ?>
                <div class="provider-featured-image__badge" title="Image selected by AI for best representation">
                    <span class="provider-featured-image__badge-icon">🎯</span>
                    <span class="provider-featured-image__badge-text">AI Selected</span>
                </div>
            <?php endif; ?>
        </div>
        
    <?php else: ?>
        
        <!-- Fallback when no image is available -->
        <div class="provider-featured-image__placeholder">
            <div class="provider-featured-image__placeholder-icon">
                🏥
            </div>
            <div class="provider-featured-image__placeholder-text">
                <strong><?php echo esc_html($provider_name); ?></strong><br>
                <span>Healthcare Provider</span>
            </div>
        </div>
        
    <?php endif; ?>
</div>

<style>
/* Provider Featured Image Block Styles */
.provider-featured-image {
    margin: 1.5rem 0;
    position: relative;
}

.provider-featured-image__container {
    position: relative;
    overflow: hidden;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    background: #f8f9fa;
}

.provider-featured-image__img {
    width: 100%;
    height: auto;
    display: block;
    transition: transform 0.3s ease;
}

.provider-featured-image__img:hover {
    transform: scale(1.02);
}

/* Image size variations */
.provider-featured-image__img--small {
    max-height: 200px;
    object-fit: cover;
}

.provider-featured-image__img--medium {
    max-height: 300px;
    object-fit: cover;
}

.provider-featured-image__img--large {
    max-height: 400px;
    object-fit: cover;
}

.provider-featured-image__img--full {
    height: auto;
}

/* Caption styling */
.provider-featured-image__caption {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
    color: white;
    padding: 1rem;
    font-size: 0.9rem;
    line-height: 1.4;
}

/* AI Selection Badge */
.provider-featured-image__badge {
    position: absolute;
    top: 12px;
    right: 12px;
    background: rgba(37, 99, 235, 0.9);
    color: white;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    display: flex;
    align-items: center;
    gap: 4px;
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    opacity: 0.8;
    transition: opacity 0.3s ease;
}

.provider-featured-image__badge:hover {
    opacity: 1;
}

.provider-featured-image__badge-icon {
    font-size: 10px;
}

.provider-featured-image__badge-text {
    font-size: 10px;
}

/* Placeholder styling */
.provider-featured-image__placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 200px;
    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
    border: 2px dashed #cbd5e1;
    border-radius: 8px;
    text-align: center;
    padding: 2rem;
    color: #64748b;
}

.provider-featured-image__placeholder-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.7;
}

.provider-featured-image__placeholder-text {
    font-size: 1.1rem;
    line-height: 1.5;
}

.provider-featured-image__placeholder-text strong {
    color: #334155;
    font-weight: 600;
}

/* Alignment styles */
.provider-featured-image.alignwide {
    width: 100vw;
    max-width: 100vw;
    margin-left: calc(50% - 50vw);
}

.provider-featured-image.alignfull {
    width: 100vw;
    max-width: 100vw;
    margin-left: calc(50% - 50vw);
}

/* Responsive design */
@media (max-width: 768px) {
    .provider-featured-image__badge {
        top: 8px;
        right: 8px;
        padding: 2px 6px;
        font-size: 10px;
    }
    
    .provider-featured-image__badge-text {
        display: none; /* Show only icon on mobile */
    }
    
    .provider-featured-image__caption {
        padding: 0.75rem;
        font-size: 0.85rem;
    }
    
    .provider-featured-image__placeholder {
        min-height: 150px;
        padding: 1.5rem;
    }
    
    .provider-featured-image__placeholder-icon {
        font-size: 2.5rem;
    }
}

/* Print styles */
@media print {
    .provider-featured-image__badge {
        display: none;
    }
    
    .provider-featured-image__img {
        box-shadow: none;
        border: 1px solid #ddd;
    }
}
</style> 