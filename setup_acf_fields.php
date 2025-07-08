<?php
/**
 * Healthcare Directory ACF Setup
 * 
 * This script sets up Advanced Custom Fields for the healthcare provider directory.
 * Run this once after ACF Pro is installed and activated.
 * 
 * Usage: Add this code to your theme's functions.php or create as a plugin
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Register ACF Field Groups for Healthcare Providers
 */
add_action('acf/init', 'healthcare_register_acf_fields');
function healthcare_register_acf_fields() {
    
    // Only proceed if ACF is available
    if (!function_exists('acf_add_local_field_group')) {
        return;
    }

    // 1. PROVIDER DETAILS FIELD GROUP
    acf_add_local_field_group(array(
        'key' => 'group_provider_details',
        'title' => 'Provider Details',
        'fields' => array(
            array(
                'key' => 'field_provider_phone',
                'label' => 'Phone Number',
                'name' => 'provider_phone',
                'type' => 'text',
                'instructions' => 'Primary contact phone number',
                'wrapper' => array('width' => '50'),
            ),
            array(
                'key' => 'field_provider_website',
                'label' => 'Website',
                'name' => 'provider_website',
                'type' => 'url',
                'instructions' => 'Official website URL',
                'wrapper' => array('width' => '50'),
            ),
            array(
                'key' => 'field_provider_address',
                'label' => 'Full Address',
                'name' => 'provider_address',
                'type' => 'textarea',
                'instructions' => 'Complete address including postal code',
                'rows' => 3,
            ),
            array(
                'key' => 'field_postal_code',
                'label' => 'Postal Code',
                'name' => 'postal_code',
                'type' => 'text',
                'instructions' => 'Japanese postal code',
                'wrapper' => array('width' => '33'),
            ),
            array(
                'key' => 'field_provider_rating',
                'label' => 'Rating',
                'name' => 'provider_rating',
                'type' => 'number',
                'instructions' => 'Average rating (0-5)',
                'min' => 0,
                'max' => 5,
                'step' => 0.1,
                'wrapper' => array('width' => '33'),
            ),
            array(
                'key' => 'field_provider_reviews',
                'label' => 'Total Reviews',
                'name' => 'provider_reviews',
                'type' => 'number',
                'instructions' => 'Total number of reviews',
                'min' => 0,
                'wrapper' => array('width' => '34'),
            ),
            array(
                'key' => 'field_wheelchair_accessible',
                'label' => 'Wheelchair Accessible',
                'name' => 'wheelchair_accessible',
                'type' => 'true_false',
                'instructions' => 'Is this facility wheelchair accessible?',
                'wrapper' => array('width' => '50'),
            ),
            array(
                'key' => 'field_parking_available',
                'label' => 'Parking Available',
                'name' => 'parking_available',
                'type' => 'true_false',
                'instructions' => 'Is parking available at this facility?',
                'wrapper' => array('width' => '50'),
            ),
            array(
                'key' => 'field_business_status',
                'label' => 'Business Status',
                'name' => 'business_status',
                'type' => 'select',
                'instructions' => 'Current operational status',
                'choices' => array(
                    'Operational' => 'Operational',
                    'Temporarily Closed' => 'Temporarily Closed',
                    'Permanently Closed' => 'Permanently Closed',
                    'Unknown' => 'Unknown',
                ),
                'wrapper' => array('width' => '50'),
            ),
            array(
                'key' => 'field_prefecture',
                'label' => 'Prefecture',
                'name' => 'prefecture',
                'type' => 'text',
                'instructions' => 'Prefecture/State location',
                'wrapper' => array('width' => '50'),
            ),
            array(
                'key' => 'field_ai_description',
                'label' => 'AI Generated Description',
                'name' => 'ai_description',
                'type' => 'textarea',
                'instructions' => 'AI-enhanced description of healthcare provider',
                'rows' => 6,
            ),
        ),
        'location' => array(
            array(
                array(
                    'param' => 'post_type',
                    'operator' => '==',
                    'value' => 'healthcare_provider',
                ),
            ),
        ),
        'menu_order' => 1,
        'position' => 'normal',
        'style' => 'default',
        'show_in_rest' => 1,
    ));

    // 2. LOCATION & NAVIGATION FIELD GROUP
    acf_add_local_field_group(array(
        'key' => 'group_location_navigation',
        'title' => 'Location & Navigation',
        'fields' => array(
            array(
                'key' => 'field_latitude',
                'label' => 'Latitude',
                'name' => 'latitude',
                'type' => 'number',
                'instructions' => 'GPS latitude coordinate',
                'step' => 0.0000001,
                'wrapper' => array('width' => '33'),
            ),
            array(
                'key' => 'field_longitude',
                'label' => 'Longitude',
                'name' => 'longitude',
                'type' => 'number',
                'instructions' => 'GPS longitude coordinate',
                'step' => 0.0000001,
                'wrapper' => array('width' => '33'),
            ),
            array(
                'key' => 'field_nearest_station',
                'label' => 'Nearest Station',
                'name' => 'nearest_station',
                'type' => 'text',
                'instructions' => 'Walking time to nearest train station',
                'wrapper' => array('width' => '34'),
            ),
            array(
                'key' => 'field_google_maps_embed',
                'label' => 'Google Maps Embed',
                'name' => 'google_maps_embed',
                'type' => 'textarea',
                'instructions' => 'Generated automatically from coordinates',
                'readonly' => 1,
                'rows' => 3,
            ),
        ),
        'location' => array(
            array(
                array(
                    'param' => 'post_type',
                    'operator' => '==',
                    'value' => 'healthcare_provider',
                ),
            ),
        ),
        'menu_order' => 2,
        'position' => 'normal',
        'style' => 'default',
        'show_in_rest' => 1,
    ));

    // 3. LANGUAGE SUPPORT FIELD GROUP
    acf_add_local_field_group(array(
        'key' => 'group_language_support',
        'title' => 'Language Support',
        'fields' => array(
            array(
                'key' => 'field_english_proficiency',
                'label' => 'English Proficiency Level',
                'name' => 'english_proficiency',
                'type' => 'select',
                'instructions' => 'Level of English language support',
                'choices' => array(
                    'Fluent' => 'Fluent',
                    'Conversational' => 'Conversational',
                    'Basic' => 'Basic',
                    'Unknown' => 'Unknown',
                ),
                'wrapper' => array('width' => '50'),
            ),
            array(
                'key' => 'field_proficiency_score',
                'label' => 'Proficiency Score',
                'name' => 'proficiency_score',
                'type' => 'number',
                'instructions' => 'Numerical score (0-100) based on evidence',
                'min' => 0,
                'max' => 100,
                'wrapper' => array('width' => '50'),
            ),
            array(
                'key' => 'field_english_indicators',
                'label' => 'English Support Evidence',
                'name' => 'english_indicators',
                'type' => 'textarea',
                'instructions' => 'Specific evidence of English language support',
                'rows' => 3,
            ),

        ),
        'location' => array(
            array(
                array(
                    'param' => 'post_type',
                    'operator' => '==',
                    'value' => 'healthcare_provider',
                ),
            ),
        ),
        'menu_order' => 3,
        'position' => 'normal',
        'style' => 'default',
        'show_in_rest' => 1,
    ));

    // 4. PHOTO GALLERY FIELD GROUP
    acf_add_local_field_group(array(
        'key' => 'group_photo_gallery',
        'title' => 'Photo Gallery',
        'fields' => array(
            array(
                'key' => 'field_photo_gallery',
                'label' => 'Provider Photos',
                'name' => 'photo_gallery',
                'type' => 'gallery',
                'instructions' => 'Photos of the healthcare facility',
                'return_format' => 'array',
                'preview_size' => 'thumbnail',
                'library' => 'all',
            ),
            array(
                'key' => 'field_photo_urls_raw',
                'label' => 'Raw Photo URLs',
                'name' => 'photo_urls',
                'type' => 'textarea',
                'instructions' => 'JSON array of photo URLs from Google Places',
                'readonly' => 1,
                'rows' => 3,
            ),
        ),
        'location' => array(
            array(
                array(
                    'param' => 'post_type',
                    'operator' => '==',
                    'value' => 'healthcare_provider',
                ),
            ),
        ),
        'menu_order' => 4,
        'position' => 'normal',
        'style' => 'default',
        'show_in_rest' => 1,
    ));

    // 5. PATIENT INSIGHTS FIELD GROUP
    acf_add_local_field_group(array(
        'key' => 'group_patient_insights',
        'title' => 'Patient Insights',
        'fields' => array(
            array(
                'key' => 'field_review_keywords',
                'label' => 'Key Patient Feedback Themes',
                'name' => 'review_keywords',
                'type' => 'textarea',
                'instructions' => 'Most mentioned keywords from patient reviews',
                'readonly' => 1,
                'rows' => 3,
            ),
            array(
                'key' => 'field_patient_highlights',
                'label' => 'Patient Experience Highlights',
                'name' => 'patient_highlights',
                'type' => 'repeater',
                'instructions' => 'Key positive aspects mentioned by patients',
                'sub_fields' => array(
                    array(
                        'key' => 'field_highlight_text',
                        'label' => 'Highlight',
                        'name' => 'highlight_text',
                        'type' => 'text',
                    ),
                    array(
                        'key' => 'field_highlight_icon',
                        'label' => 'Icon',
                        'name' => 'highlight_icon',
                        'type' => 'text',
                        'instructions' => 'Emoji or icon for this highlight',
                        'wrapper' => array('width' => '20'),
                    ),
                ),
                'min' => 0,
                'max' => 6,
                'layout' => 'table',
                'button_label' => 'Add Highlight',
            ),
        ),
        'location' => array(
            array(
                array(
                    'param' => 'post_type',
                    'operator' => '==',
                    'value' => 'healthcare_provider',
                ),
            ),
        ),
        'menu_order' => 5,
        'position' => 'normal',
        'style' => 'default',
        'show_in_rest' => 1,
    ));
}

/**
 * Register ACF Blocks for Healthcare Providers
 */
add_action('acf/init', 'healthcare_register_acf_blocks');
function healthcare_register_acf_blocks() {
    
    // Check if function exists
    if (!function_exists('acf_register_block_type')) {
        return;
    }

    // 1. PROVIDER CONTACT INFO BLOCK
    acf_register_block_type(array(
        'name' => 'provider-contact',
        'title' => __('Provider Contact Info'),
        'description' => __('Display provider contact information and details'),
        'render_template' => get_stylesheet_directory() . '/blocks/provider-contact.php',
        'category' => 'healthcare',
        'icon' => 'phone',
        'keywords' => array('contact', 'phone', 'healthcare', 'provider'),
        'supports' => array(
            'align' => array('wide', 'full'),
            'anchor' => true,
        ),
    ));

    // 2. GOOGLE MAPS BLOCK
    acf_register_block_type(array(
        'name' => 'provider-map',
        'title' => __('Provider Location Map'),
        'description' => __('Display interactive Google Map for provider location'),
        'render_template' => get_stylesheet_directory() . '/blocks/provider-map.php',
        'category' => 'healthcare',
        'icon' => 'location-alt',
        'keywords' => array('map', 'location', 'healthcare', 'provider'),
        'supports' => array(
            'align' => array('wide', 'full'),
            'anchor' => true,
        ),
    ));

    // 3. LANGUAGE SUPPORT BLOCK
    acf_register_block_type(array(
        'name' => 'language-support',
        'title' => __('Language Support Info'),
        'description' => __('Display English and language support information'),
        'render_template' => get_stylesheet_directory() . '/blocks/language-support.php',
        'category' => 'healthcare',
        'icon' => 'translation',
        'keywords' => array('language', 'english', 'healthcare', 'support'),
        'supports' => array(
            'align' => array('wide', 'full'),
            'anchor' => true,
        ),
    ));

    // 4. PHOTO GALLERY BLOCK
    acf_register_block_type(array(
        'name' => 'provider-gallery',
        'title' => __('Provider Photo Gallery'),
        'description' => __('Display photo gallery of healthcare facility'),
        'render_template' => get_stylesheet_directory() . '/blocks/provider-gallery.php',
        'category' => 'healthcare',
        'icon' => 'format-gallery',
        'keywords' => array('photos', 'gallery', 'healthcare', 'facility'),
        'supports' => array(
            'align' => array('wide', 'full'),
            'anchor' => true,
        ),
    ));

    // 5. PATIENT INSIGHTS BLOCK
    acf_register_block_type(array(
        'name' => 'patient-insights',
        'title' => __('Patient Experience Insights'),
        'description' => __('Display key patient feedback and experience highlights'),
        'render_template' => get_stylesheet_directory() . '/blocks/patient-insights.php',
        'category' => 'healthcare',
        'icon' => 'star-filled',
        'keywords' => array('reviews', 'patient', 'experience', 'feedback'),
        'supports' => array(
            'align' => array('wide', 'full'),
            'anchor' => true,
        ),
    ));

    // 6. PROVIDER DESCRIPTION BLOCK
    acf_register_block_type(array(
        'name' => 'provider-description',
        'title' => __('Provider AI Description'),
        'description' => __('Display AI-generated provider description and overview'),
        'render_template' => get_stylesheet_directory() . '/blocks/provider-description.php',
        'category' => 'healthcare',
        'icon' => 'editor-alignleft',
        'keywords' => array('description', 'ai', 'overview', 'about'),
        'supports' => array(
            'align' => array('wide', 'full'),
            'anchor' => true,
        ),
    ));

    // 7. PROVIDER CALL-TO-ACTION BLOCK
    acf_register_block_type(array(
        'name' => 'provider-cta',
        'title' => __('Provider Call-to-Action'),
        'description' => __('Display appointment booking and contact call-to-action'),
        'render_template' => get_stylesheet_directory() . '/blocks/provider-cta.php',
        'category' => 'healthcare',
        'icon' => 'megaphone',
        'keywords' => array('appointment', 'booking', 'call', 'cta', 'contact'),
        'supports' => array(
            'align' => array('wide', 'full'),
            'anchor' => true,
        ),
    ));

    // 8. PROVIDER FEATURED IMAGE BLOCK
    acf_register_block_type(array(
        'name' => 'provider-featured-image',
        'title' => __('Provider Featured Image'),
        'description' => __('Display provider featured image with size and placement control'),
        'render_template' => get_stylesheet_directory() . '/blocks/provider-featured-image.php',
        'category' => 'healthcare',
        'icon' => 'format-image',
        'keywords' => array('image', 'photo', 'featured', 'facility', 'picture'),
        'supports' => array(
            'align' => array('wide', 'full'),
            'anchor' => true,
        ),
    ));
}

/**
 * Add custom block category for healthcare blocks
 */
add_filter('block_categories_all', 'healthcare_add_block_category', 10, 2);
function healthcare_add_block_category($categories, $post) {
    return array_merge(
        array(
            array(
                'slug' => 'healthcare',
                'title' => __('Healthcare Directory'),
                'icon' => 'heart',
            ),
        ),
        $categories
    );
}

/**
 * Auto-populate ACF fields from post meta when editing
 */
add_action('acf/load_value', 'healthcare_populate_acf_from_meta', 10, 3);
function healthcare_populate_acf_from_meta($value, $post_id, $field) {
    
    // Only for healthcare_provider posts
    if (get_post_type($post_id) !== 'healthcare_provider') {
        return $value;
    }
    
    // Map ACF field names to post meta keys - Complete mapping for all sync'd fields
    $field_map = array(
        // Provider Details Field Group
        'provider_phone' => 'provider_phone',
        'provider_website' => 'provider_website',
        'provider_address' => 'provider_address',
        'provider_rating' => 'provider_rating',
        'provider_reviews' => 'provider_reviews',
        'wheelchair_accessible' => 'wheelchair_accessible',
        'parking_available' => 'parking_available',
        'business_status' => 'business_status',
        'prefecture' => 'prefecture',
        'postal_code' => 'postal_code',
        'ai_description' => 'ai_description',
        
        // Location & Navigation Field Group
        'latitude' => 'latitude',
        'longitude' => 'longitude',
        'nearest_station' => 'nearest_station',
        
        // Language Support Field Group
        'english_proficiency' => 'english_proficiency',
        'proficiency_score' => 'proficiency_score',
        'english_indicators' => 'english_indicators',
        
        // Photo Gallery Field Group
        'photo_urls' => 'photo_urls',
        
        // Patient Insights Field Group
        'review_keywords' => 'review_keywords',
    );
    
    // If this field should be populated from meta and value is empty
    if (isset($field_map[$field['name']]) && empty($value)) {
        $meta_value = get_post_meta($post_id, $field_map[$field['name']], true);
        
        // Handle JSON fields
        if (in_array($field['name'], ['english_indicators', 'review_keywords']) && !empty($meta_value)) {
            $decoded = json_decode($meta_value, true);
            if (is_array($decoded)) {
                return $field['name'] === 'english_indicators' ? implode("\n", $decoded) : $meta_value;
            }
        }
        
        // Handle boolean fields
        if (in_array($field['name'], ['wheelchair_accessible', 'parking_available'])) {
            return $meta_value === 'True' || $meta_value === '1' || $meta_value === true;
        }
        
        return $meta_value;
    }
    
    return $value;
}

/**
 * Generate Google Maps embed code from coordinates
 */
add_filter('acf/load_value/name=google_maps_embed', 'healthcare_generate_maps_embed', 10, 3);
function healthcare_generate_maps_embed($value, $post_id, $field) {
    
    if (get_post_type($post_id) !== 'healthcare_provider') {
        return $value;
    }
    
    $lat = get_post_meta($post_id, 'latitude', true);
    $lng = get_post_meta($post_id, 'longitude', true);
    $name = get_the_title($post_id);
    
    if ($lat && $lng) {
        $embed_url = "https://www.google.com/maps/embed/v1/place";
        $api_key = "YOUR_GOOGLE_MAPS_API_KEY"; // You'll need to add your API key
        $query = urlencode($name . " " . $lat . "," . $lng);
        
        $embed_code = "<iframe width=\"100%\" height=\"300\" frameborder=\"0\" style=\"border:0\" src=\"{$embed_url}?key={$api_key}&q={$query}&zoom=15\" allowfullscreen></iframe>";
        
        return $embed_code;
    }
    
    return $value;
}

/**
 * Remove automatic featured image display for healthcare providers
 * This gives complete control to the custom featured image block
 */
add_action('wp_head', 'healthcare_remove_featured_image_display');
function healthcare_remove_featured_image_display() {
    if (is_singular('healthcare_provider')) {
        // Remove featured image from theme display
        remove_action('blocksy:single:featured-image', 'blocksy_post_featured_image');
        
        // Remove post thumbnail support for this post type during display
        add_filter('post_thumbnail_html', 'healthcare_remove_post_thumbnail', 10, 5);
    }
}

/**
 * Filter to remove post thumbnail display for healthcare providers
 */
function healthcare_remove_post_thumbnail($html, $post_id, $post_thumbnail_id, $size, $attr) {
    if (get_post_type($post_id) === 'healthcare_provider') {
        return ''; // Return empty string to hide featured image
    }
    return $html;
}

/**
 * Remove featured image from theme's post content for healthcare providers
 */
add_filter('the_content', 'healthcare_filter_content_featured_image');
function healthcare_filter_content_featured_image($content) {
    if (is_singular('healthcare_provider') && in_the_loop() && is_main_query()) {
        // Remove any automatic featured image insertion in content
        remove_filter('the_content', 'prepend_attachment');
    }
    return $content;
}

/**
 * Hide featured image in admin for healthcare providers (optional)
 */
add_action('do_meta_boxes', 'healthcare_remove_featured_image_metabox');
function healthcare_remove_featured_image_metabox() {
    $post_type = 'healthcare_provider';
    remove_meta_box('postimagediv', $post_type, 'side');
}

/**
 * Add custom metabox to explain featured image usage
 */
add_action('add_meta_boxes', 'healthcare_add_featured_image_info');
function healthcare_add_featured_image_info() {
    add_meta_box(
        'healthcare_featured_image_info',
        'Featured Image Info',
        'healthcare_featured_image_info_callback',
        'healthcare_provider',
        'side',
        'low'
    );
}

function healthcare_featured_image_info_callback($post) {
    $featured_image_id = get_post_thumbnail_id($post->ID);
    if ($featured_image_id) {
        $image_url = wp_get_attachment_image_src($featured_image_id, 'thumbnail')[0];
        echo '<div style="text-align: center; padding: 10px;">';
        echo '<img src="' . esc_url($image_url) . '" style="max-width: 100%; height: auto; border-radius: 4px; margin-bottom: 10px;">';
        echo '<p><strong>✅ Featured image is set</strong></p>';
        echo '<p><small>Use the "Provider Featured Image" block to display this image on your page.</small></p>';
        echo '</div>';
    } else {
        echo '<div style="text-align: center; padding: 15px; background: #f0f0f1; border-radius: 4px;">';
        echo '<p><strong>No featured image</strong></p>';
        echo '<p><small>Featured images are automatically set during sync from facility photos.</small></p>';
        echo '</div>';
    }
}


