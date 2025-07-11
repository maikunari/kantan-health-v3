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
                'type' => 'select',
                'instructions' => 'Wheelchair accessibility status',
                'choices' => array(
                    'Wheelchair accessible' => 'Wheelchair accessible',
                    'Not wheelchair accessible' => 'Not wheelchair accessible',
                    'Wheelchair accessibility unknown' => 'Wheelchair accessibility unknown',
                ),
                'default_value' => 'Wheelchair accessibility unknown',
                'wrapper' => array('width' => '50'),
            ),
            array(
                'key' => 'field_parking_available',
                'label' => 'Parking Available',
                'name' => 'parking_available',
                'type' => 'select',
                'instructions' => 'Parking availability status',
                'choices' => array(
                    'Parking is available' => 'Parking is available',
                    'Parking is not available' => 'Parking is not available',
                    'Parking unknown' => 'Parking unknown',
                ),
                'default_value' => 'Parking unknown',
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
                'type' => 'wysiwyg',
                'instructions' => 'AI-enhanced description of healthcare provider',
                'tabs' => 'visual',
                'toolbar' => 'basic',
                'media_upload' => 0,
                'delay' => 0,
            ),
            array(
                'key' => 'field_ai_excerpt',
                'label' => 'AI Generated Excerpt',
                'name' => 'ai_excerpt',
                'type' => 'textarea',
                'instructions' => 'AI-generated summary/preview of healthcare provider',
                'rows' => 4,
                'maxlength' => 600,
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
                'instructions' => 'Geographic latitude coordinate',
                'step' => 0.000001,
                'wrapper' => array('width' => '33'),
            ),
            array(
                'key' => 'field_longitude',
                'label' => 'Longitude',
                'name' => 'longitude',
                'type' => 'number',
                'instructions' => 'Geographic longitude coordinate',
                'step' => 0.000001,
                'wrapper' => array('width' => '33'),
            ),
            array(
                'key' => 'field_district',
                'label' => 'District/Ward',
                'name' => 'district',
                'type' => 'text',
                'instructions' => 'District or ward within the city (e.g., Shibuya, Minato)',
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

    // 3. BUSINESS HOURS FIELD GROUP
    acf_add_local_field_group(array(
        'key' => 'group_business_hours',
        'title' => 'Business Hours',
        'fields' => array(
            array(
                'key' => 'field_business_hours',
                'label' => 'Complete Business Hours',
                'name' => 'business_hours',
                'type' => 'textarea',
                'instructions' => 'Complete formatted business hours for all days',
                'rows' => 8,
                'wrapper' => array('width' => '100'),
            ),
            array(
                'key' => 'field_hours_monday',
                'label' => 'Monday Hours',
                'name' => 'hours_monday',
                'type' => 'text',
                'instructions' => 'Monday operating hours',
                'wrapper' => array('width' => '50'),
            ),
            array(
                'key' => 'field_hours_tuesday',
                'label' => 'Tuesday Hours',
                'name' => 'hours_tuesday',
                'type' => 'text',
                'instructions' => 'Tuesday operating hours',
                'wrapper' => array('width' => '50'),
            ),
            array(
                'key' => 'field_hours_wednesday',
                'label' => 'Wednesday Hours',
                'name' => 'hours_wednesday',
                'type' => 'text',
                'instructions' => 'Wednesday operating hours',
                'wrapper' => array('width' => '50'),
            ),
            array(
                'key' => 'field_hours_thursday',
                'label' => 'Thursday Hours',
                'name' => 'hours_thursday',
                'type' => 'text',
                'instructions' => 'Thursday operating hours',
                'wrapper' => array('width' => '50'),
            ),
            array(
                'key' => 'field_hours_friday',
                'label' => 'Friday Hours',
                'name' => 'hours_friday',
                'type' => 'text',
                'instructions' => 'Friday operating hours',
                'wrapper' => array('width' => '50'),
            ),
            array(
                'key' => 'field_hours_saturday',
                'label' => 'Saturday Hours',
                'name' => 'hours_saturday',
                'type' => 'text',
                'instructions' => 'Saturday operating hours',
                'wrapper' => array('width' => '50'),
            ),
            array(
                'key' => 'field_hours_sunday',
                'label' => 'Sunday Hours',
                'name' => 'hours_sunday',
                'type' => 'text',
                'instructions' => 'Sunday operating hours',
                'wrapper' => array('width' => '50'),
            ),
            array(
                'key' => 'field_open_now',
                'label' => 'Open Now Status',
                'name' => 'open_now',
                'type' => 'select',
                'instructions' => 'Current open/closed status',
                'choices' => array(
                    'Open Now' => 'Currently Open',
                    'Closed' => 'Currently Closed',
                    'Status unknown' => 'Status Unknown',
                ),
                'default_value' => 'Status unknown',
                'wrapper' => array('width' => '50'),
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

    // 4. LANGUAGE SUPPORT FIELD GROUP
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
                'instructions' => 'Numerical score (0-5): 0=Unknown, 3=Basic, 4=Conversational, 5=Fluent',
                'min' => 0,
                'max' => 5,
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
        'menu_order' => 4,
        'position' => 'normal',
        'style' => 'default',
        'show_in_rest' => 1,
    ));

    // 5. PHOTO GALLERY FIELD GROUP  
    acf_add_local_field_group(array(
        'key' => 'group_photo_gallery',
        'title' => 'Photo Gallery & Featured Image',
        'fields' => array(
            array(
                'key' => 'field_photo_urls',
                'label' => 'Photo URLs',
                'name' => 'photo_urls',
                'type' => 'textarea',
                'instructions' => 'Google Places photo URLs (one per line)',
                'rows' => 5,
                'wrapper' => array('width' => '100'),
            ),
            array(
                'key' => 'field_external_featured_image',
                'label' => 'External Featured Image URL',
                'name' => 'external_featured_image',
                'type' => 'url',
                'instructions' => 'Claude AI-selected or primary photo URL (automatically managed)',
                'readonly' => 1,
                'wrapper' => array('width' => '70'),
            ),
            array(
                'key' => 'field_featured_image_source',
                'label' => 'Featured Image Source',
                'name' => 'featured_image_source',
                'type' => 'select',
                'instructions' => 'Source of the featured image selection',
                'choices' => array(
                    'Claude AI Selected' => 'Claude AI Selected',
                    'First Available Photo' => 'First Available Photo',
                    'Manual Selection' => 'Manual Selection',
                    'No Image Available' => 'No Image Available',
                ),
                'readonly' => 1,
                'default_value' => 'No Image Available',
                'wrapper' => array('width' => '30'),
            ),
            array(
                'key' => 'field_photo_count',
                'label' => 'Available Photos',
                'name' => 'photo_count',
                'type' => 'number',
                'instructions' => 'Number of photos available from Google Places',
                'readonly' => 1,
                'min' => 0,
                'wrapper' => array('width' => '20'),
            ),
            array(
                'key' => 'field_image_selection_status',
                'label' => 'Image Selection Status',
                'name' => 'image_selection_status',
                'type' => 'select',
                'instructions' => 'Status of AI image selection process',
                'choices' => array(
                    'pending' => 'Pending Selection',
                    'selected' => 'AI Selected',
                    'fallback' => 'Using Fallback',
                    'none' => 'No Images Available',
                ),
                'readonly' => 1,
                'default_value' => 'pending',
                'wrapper' => array('width' => '30'),
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

    // 6. PATIENT INSIGHTS FIELD GROUP
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
                'key' => 'field_review_summary',
                'label' => 'Patient Review Summary',
                'name' => 'review_summary',
                'type' => 'textarea',
                'instructions' => 'AI-generated narrative summary of patient reviews (80-100 words)',
                'readonly' => 1,
                'rows' => 5,
            ),
            array(
                'key' => 'field_english_experience_summary',
                'label' => 'English Language Experience',
                'name' => 'english_experience_summary',
                'type' => 'textarea',
                'instructions' => 'AI-generated summary of English language support and communication experience (80-100 words)',
                'readonly' => 1,
                'rows' => 5,
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
        'menu_order' => 6,
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

    // Add fields for Provider Featured Image Block
    acf_add_local_field_group(array(
        'key' => 'group_provider_featured_image_block',
        'title' => 'Provider Featured Image Block Settings',
        'fields' => array(
            array(
                'key' => 'field_image_size',
                'label' => 'Image Size',
                'name' => 'image_size',
                'type' => 'select',
                'instructions' => 'Choose how the featured image should be displayed',
                'choices' => array(
                    'small' => 'Small (200px height)',
                    'medium' => 'Medium (300px height)',
                    'large' => 'Large (400px height)',
                    'full' => 'Full Size (original aspect ratio)',
                ),
                'default_value' => 'large',
            ),
            array(
                'key' => 'field_show_caption',
                'label' => 'Show Caption',
                'name' => 'show_caption',
                'type' => 'true_false',
                'instructions' => 'Display a caption overlay on the image',
                'default_value' => 0,
            ),
            array(
                'key' => 'field_image_caption',
                'label' => 'Image Caption',
                'name' => 'image_caption',
                'type' => 'textarea',
                'instructions' => 'Caption text to display over the image (HTML allowed)',
                'rows' => 3,
                'conditional_logic' => array(
                    array(
                        array(
                            'field' => 'field_show_caption',
                            'operator' => '==',
                            'value' => '1',
                        ),
                    ),
                ),
            ),
            array(
                'key' => 'field_show_ai_badge',
                'label' => 'Show AI Selection Badge',
                'name' => 'show_ai_badge',
                'type' => 'true_false',
                'instructions' => 'Display badge when image was selected by Claude AI',
                'default_value' => 1,
                'message' => 'Show "AI Selected" badge for Claude-chosen images',
            ),
        ),
        'location' => array(
            array(
                array(
                    'param' => 'block',
                    'operator' => '==',
                    'value' => 'acf/provider-featured-image',
                ),
            ),
        ),
        'menu_order' => 0,
        'position' => 'normal',
        'style' => 'default',
        'show_in_rest' => 1,
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
        'ai_description' => 'ai_description',
        'ai_excerpt' => 'ai_excerpt',
        
        // Location & Navigation Field Group
        'latitude' => 'latitude',
        'longitude' => 'longitude',
        'district' => 'district',
        'nearest_station' => 'nearest_station',
        
        // Language Support Field Group
        'english_proficiency' => 'english_proficiency',
        'proficiency_score' => 'proficiency_score',
        'english_indicators' => 'english_indicators',
        
        // Photo Gallery Field Group
        'photo_urls' => 'photo_urls',
        'external_featured_image' => 'external_featured_image',
        'featured_image_source' => 'featured_image_source',
        'photo_count' => 'photo_count',
        'image_selection_status' => 'image_selection_status',
        
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
 * Sync ACF excerpt field to native WordPress excerpt
 */
add_action('acf/save_post', 'healthcare_sync_excerpt_to_native', 20);
function healthcare_sync_excerpt_to_native($post_id) {
    // Only for healthcare_provider posts
    if (get_post_type($post_id) !== 'healthcare_provider') {
        return;
    }
    
    // Get the ACF excerpt field value
    $acf_excerpt = get_field('ai_excerpt', $post_id);
    
    // If ACF excerpt exists, sync it to native WordPress excerpt
    if (!empty($acf_excerpt)) {
        // Remove this hook temporarily to prevent infinite loop
        remove_action('acf/save_post', 'healthcare_sync_excerpt_to_native', 20);
        
        // Update the native WordPress excerpt
        wp_update_post(array(
            'ID' => $post_id,
            'post_excerpt' => $acf_excerpt
        ));
        
        // Re-add the hook
        add_action('acf/save_post', 'healthcare_sync_excerpt_to_native', 20);
    }
}

/**
 * Sync native WordPress excerpt to ACF excerpt field
 */
add_action('save_post', 'healthcare_sync_native_to_excerpt', 20);
function healthcare_sync_native_to_excerpt($post_id) {
    // Only for healthcare_provider posts
    if (get_post_type($post_id) !== 'healthcare_provider') {
        return;
    }
    
    // Skip if this is an autosave
    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
        return;
    }
    
    // Get the native WordPress excerpt
    $native_excerpt = get_post_field('post_excerpt', $post_id);
    
    // If native excerpt exists and ACF excerpt is empty, sync it
    if (!empty($native_excerpt)) {
        $acf_excerpt = get_field('ai_excerpt', $post_id);
        if (empty($acf_excerpt)) {
            update_field('ai_excerpt', $native_excerpt, $post_id);
        }
    }
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
 * Ensure excerpt metabox is visible for healthcare providers
 */
add_action('add_meta_boxes', 'healthcare_add_excerpt_metabox');
function healthcare_add_excerpt_metabox() {
    add_meta_box(
        'postexcerpt',
        __('Excerpt'),
        'post_excerpt_meta_box',
        'healthcare_provider',
        'normal',
        'core'
    );
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


/**
 * EXTERNAL FEATURED IMAGE SYSTEM (Google Places TOS Compliant)
 * Allows featured images to be set using external URLs without importing to media library
 */

/**
 * Override post thumbnail HTML to use external featured image when available
 */
add_filter('post_thumbnail_html', 'healthcare_external_featured_image', 10, 5);
function healthcare_external_featured_image($html, $post_id, $post_thumbnail_id, $size, $attr) {
    // Only for healthcare providers
    if (get_post_type($post_id) !== 'healthcare_provider') {
        return $html;
    }
    
    // If there's already a featured image, use it
    if (!empty($html)) {
        return $html;
    }
    
    // Get external featured image URL
    $external_image_url = get_post_meta($post_id, 'external_featured_image', true);
    
    if (!empty($external_image_url)) {
        $provider_name = get_the_title($post_id);
        
        // Build image attributes
        $default_attr = array(
            'alt' => esc_attr($provider_name . ' - Healthcare Provider'),
            'title' => esc_attr($provider_name),
            'class' => 'wp-post-image external-featured-image'
        );
        
        // Merge with provided attributes
        $attr = wp_parse_args($attr, $default_attr);
        
        // Build HTML attributes string
        $attr_string = '';
        foreach ($attr as $key => $value) {
            $attr_string .= $key . '="' . esc_attr($value) . '" ';
        }
        
        // Return external image HTML
        return '<img src="' . esc_url($external_image_url) . '" ' . $attr_string . '/>';
    }
    
    return $html;
}

/**
 * Add external featured image support to has_post_thumbnail function
 */
add_filter('has_post_thumbnail', 'healthcare_has_external_featured_image', 10, 2);
function healthcare_has_external_featured_image($has_thumbnail, $post_id) {
    // Only for healthcare providers
    if (get_post_type($post_id) !== 'healthcare_provider') {
        return $has_thumbnail;
    }
    
    // If already has thumbnail, return true
    if ($has_thumbnail) {
        return true;
    }
    
    // Check for external featured image
    $external_image_url = get_post_meta($post_id, 'external_featured_image', true);
    
    return !empty($external_image_url);
}

/**
 * Override get_the_post_thumbnail to use external image
 */
add_filter('get_the_post_thumbnail', 'healthcare_get_external_post_thumbnail', 10, 5);
function healthcare_get_external_post_thumbnail($html, $post_id, $size, $attr) {
    // Only for healthcare providers
    if (get_post_type($post_id) !== 'healthcare_provider') {
        return $html;
    }
    
    // If there's already thumbnail HTML, use it
    if (!empty($html)) {
        return $html;
    }
    
    // Get external featured image
    $external_image_url = get_post_meta($post_id, 'external_featured_image', true);
    
    if (!empty($external_image_url)) {
        $provider_name = get_the_title($post_id);
        
        // Handle different size parameters
        $width = '';
        $height = '';
        
        if (is_array($size)) {
            $width = 'width="' . esc_attr($size[0]) . '"';
            $height = 'height="' . esc_attr($size[1]) . '"';
        } elseif (is_string($size)) {
            // Handle named sizes (thumbnail, medium, large, full)
            switch ($size) {
                case 'thumbnail':
                    $width = 'width="150"';
                    $height = 'height="150"';
                    break;
                case 'medium':
                    $width = 'width="300"';
                    $height = 'height="300"';
                    break;
                case 'large':
                    $width = 'width="600"';
                    $height = 'height="400"';
                    break;
                default:
                    // Full size - no width/height restrictions
                    break;
            }
        }
        
        // Build image attributes
        $default_attr = array(
            'alt' => esc_attr($provider_name . ' - Healthcare Provider'),
            'title' => esc_attr($provider_name),
            'class' => 'wp-post-image external-featured-image'
        );
        
        // Merge with provided attributes
        $attr = wp_parse_args($attr, $default_attr);
        
        // Build HTML attributes string
        $attr_string = '';
        foreach ($attr as $key => $value) {
            $attr_string .= $key . '="' . esc_attr($value) . '" ';
        }
        
        // Return external image HTML
        return '<img src="' . esc_url($external_image_url) . '" ' . $width . ' ' . $height . ' ' . $attr_string . '/>';
    }
    
    return $html;
}

/**
 * Add external featured image info to admin metabox
 */
add_action('add_meta_boxes', 'healthcare_add_external_featured_image_info');
function healthcare_add_external_featured_image_info() {
    add_meta_box(
        'healthcare_external_featured_image_info',
        'External Featured Image (Google Places)',
        'healthcare_external_featured_image_info_callback',
        'healthcare_provider',
        'side',
        'low'
    );
}

function healthcare_external_featured_image_info_callback($post) {
    $external_image_url = get_post_meta($post->ID, 'external_featured_image', true);
    
    if (!empty($external_image_url)) {
        echo '<div style="text-align: center; padding: 10px;">';
        echo '<img src="' . esc_url($external_image_url) . '" style="max-width: 100%; height: auto; border-radius: 4px; margin-bottom: 10px;">';
        echo '<p><strong>✅ External featured image loaded</strong></p>';
        echo '<p><small>Source: Google Places (TOS compliant)</small></p>';
        echo '<p><small>URL: ' . esc_html($external_image_url) . '</small></p>';
        echo '</div>';
    } else {
        echo '<div style="text-align: center; padding: 15px; background: #f0f0f1; border-radius: 4px;">';
        echo '<p><strong>No external featured image</strong></p>';
        echo '<p><small>External featured images are automatically set during sync from Google Places photos.</small></p>';
        echo '</div>';
    }
}

/**
 * Add CSS for external featured images
 */
add_action('wp_head', 'healthcare_external_featured_image_css');
function healthcare_external_featured_image_css() {
    if (is_singular('healthcare_provider')) {
        echo '<style>
            .external-featured-image {
                object-fit: cover;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
            }
            .external-featured-image:hover {
                transform: scale(1.02);
            }
        </style>';
    }
}


