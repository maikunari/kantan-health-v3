<?php
/**
 * Plugin Name: Healthcare Schema Generator v2
 * Plugin URI: https://care-compass.jp
 * Description: Automatically generates Schema.org markup for healthcare provider pages using ACF fields. Updated with correct field mappings for Care Compass Japan.
 * Version: 2.0.0
 * Author: Care Compass Japan
 * License: GPL v2 or later
 * 
 * This plugin automatically creates structured data (Schema.org) for healthcare provider pages
 * to improve search engine visibility and create rich snippets in Google search results.
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

class HealthcareSchemaGeneratorV2 {
    
    public function __init() {
        add_action('wp_head', array($this, 'output_provider_schema'));
        add_action('wp_head', array($this, 'output_homepage_schema'));
    }
    
    /**
     * Output schema for individual healthcare provider pages
     */
    public function output_provider_schema() {
        // Only run on healthcare provider post type
        if (!is_singular('healthcare_provider')) {
            return;
        }
        
        global $post;
        
        // Get ACF fields (using correct ACF field names)
        $provider_name = get_the_title();
        $ai_description = get_field('ai_description');
        $ai_excerpt = get_field('ai_excerpt');
        $review_summary = get_field('review_summary');
        $english_experience_summary = get_field('english_experience_summary');
        $address = get_field('provider_address');
        $phone = get_field('provider_phone');
        $website = get_field('provider_website');
        $latitude = get_field('latitude');
        $longitude = get_field('longitude');
        $business_hours = get_field('business_hours');
        $rating = get_field('provider_rating');
        $review_count = get_field('provider_reviews');
        $english_proficiency = get_field('english_proficiency');
        $proficiency_score = get_field('proficiency_score');
        $nearest_station = get_field('nearest_station');
        $wheelchair_accessible = get_field('wheelchair_accessible');
        $parking_available = get_field('parking_available');
        $district = get_field('district');
        
        // Build schema data
        $schema = array(
            '@context' => 'https://schema.org',
            '@type' => 'MedicalOrganization',
            'name' => $provider_name,
            'url' => get_permalink(),
        );
        
        // Add description (prioritize ai_description, fallback to ai_excerpt)
        if (!empty($ai_description)) {
            $schema['description'] = wp_strip_all_tags($ai_description);
        } elseif (!empty($ai_excerpt)) {
            $schema['description'] = wp_strip_all_tags($ai_excerpt);
        }
        
        // Add additional description from review summary for enhanced context
        if (!empty($review_summary)) {
            $schema['additionalProperty'][] = array(
                '@type' => 'PropertyValue',
                'name' => 'Patient Reviews Summary',
                'value' => wp_strip_all_tags($review_summary)
            );
        }
        
        // Add English experience summary as additional context
        if (!empty($english_experience_summary)) {
            $schema['additionalProperty'][] = array(
                '@type' => 'PropertyValue', 
                'name' => 'English Language Support',
                'value' => wp_strip_all_tags($english_experience_summary)
            );
        }
        
        // Add address information
        if (!empty($address)) {
            $postal_address = array(
                '@type' => 'PostalAddress',
                'streetAddress' => $address,
                'addressCountry' => 'JP'
            );
            
            // Try to extract city from address or use district
            if (!empty($district)) {
                $postal_address['addressLocality'] = $district;
            }
            
            $schema['address'] = $postal_address;
        }
        
        // Add contact information
        if (!empty($phone)) {
            $schema['telephone'] = $phone;
        }
        
        if (!empty($website)) {
            $schema['sameAs'] = $website;
        }
        
        // Add geographic coordinates
        if (!empty($latitude) && !empty($longitude)) {
            $schema['geo'] = array(
                '@type' => 'GeoCoordinates',
                'latitude' => floatval($latitude),
                'longitude' => floatval($longitude)
            );
        }
        
        // Add business hours (if structured data exists)
        if (!empty($business_hours)) {
            $opening_hours = $this->format_business_hours($business_hours);
            if (!empty($opening_hours)) {
                $schema['openingHours'] = $opening_hours;
            }
        }
        
        // Add rating information with review count
        if (!empty($rating) && is_numeric($rating)) {
            $rating_schema = array(
                '@type' => 'AggregateRating',
                'ratingValue' => floatval($rating),
                'bestRating' => '5',
                'worstRating' => '1'
            );
            
            // Add review count if available
            if (!empty($review_count) && is_numeric($review_count)) {
                $rating_schema['reviewCount'] = intval($review_count);
            }
            
            $schema['aggregateRating'] = $rating_schema;
        }
        
        // Add English language capability with proficiency score
        if (!empty($english_proficiency)) {
            $language_schema = array(
                array(
                    '@type' => 'Language',
                    'name' => 'English',
                    'proficiency' => $english_proficiency
                ),
                array(
                    '@type' => 'Language', 
                    'name' => 'Japanese'
                )
            );
            
            // Add numerical proficiency score as additional property
            if (!empty($proficiency_score) && is_numeric($proficiency_score)) {
                $schema['additionalProperty'][] = array(
                    '@type' => 'PropertyValue',
                    'name' => 'English Proficiency Score',
                    'value' => intval($proficiency_score),
                    'maxValue' => 5,
                    'minValue' => 0
                );
            }
            
            $schema['availableLanguage'] = $language_schema;
        }
        
        // Add accessibility features
        if (!empty($wheelchair_accessible)) {
            $is_accessible = ($wheelchair_accessible === 'yes' || $wheelchair_accessible === true || $wheelchair_accessible === 'true');
            if ($is_accessible) {
                $schema['accessibilityFeature'] = 'wheelchair accessible';
            }
        }
        
        // Add parking amenity
        if (!empty($parking_available)) {
            $has_parking = ($parking_available === 'yes' || $parking_available === true || $parking_available === 'true');
            $schema['amenityFeature'] = array(
                '@type' => 'LocationFeatureSpecification',
                'name' => 'Parking',
                'value' => $has_parking
            );
        }
        
        // Add nearest station for transit accessibility
        if (!empty($nearest_station)) {
            $schema['additionalProperty'][] = array(
                '@type' => 'PropertyValue',
                'name' => 'Nearest Station',
                'value' => $nearest_station
            );
        }
        
        // Add additional properties for medical organizations
        $schema['@id'] = get_permalink() . '#organization';
        $schema['identifier'] = get_the_ID();
        
        // Add Care Compass specific branding
        $schema['additionalProperty'][] = array(
            '@type' => 'PropertyValue',
            'name' => 'Directory Source',
            'value' => 'Care Compass Japan - Verified English-Speaking Healthcare'
        );
        
        // Output the schema
        echo '<script type="application/ld+json">';
        echo wp_json_encode($schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
        echo '</script>' . "\n";
    }
    
    /**
     * Output schema for homepage
     */
    public function output_homepage_schema() {
        // Only run on homepage
        if (!is_front_page()) {
            return;
        }
        
        $site_name = get_bloginfo('name') ?: 'Care Compass Japan';
        $site_description = get_bloginfo('description') ?: 'Find verified English-speaking healthcare providers in Japan';
        $site_url = home_url();
        
        // Website Schema
        $website_schema = array(
            '@context' => 'https://schema.org',
            '@type' => 'WebSite',
            'name' => $site_name,
            'description' => $site_description,
            'url' => $site_url,
            'potentialAction' => array(
                '@type' => 'SearchAction',
                'target' => array(
                    '@type' => 'EntryPoint',
                    'urlTemplate' => $site_url . '/?s={search_term_string}'
                ),
                'query-input' => 'required name=search_term_string'
            )
        );
        
        // Medical Organization Schema for Care Compass directory
        $organization_schema = array(
            '@context' => 'https://schema.org',
            '@type' => 'MedicalOrganization',
            'name' => $site_name,
            'description' => 'Comprehensive directory of verified English-speaking healthcare providers in Japan for international patients',
            'url' => $site_url,
            'areaServed' => array(
                array('@type' => 'City', 'name' => 'Tokyo'),
                array('@type' => 'City', 'name' => 'Osaka'), 
                array('@type' => 'City', 'name' => 'Yokohama'),
                array('@type' => 'City', 'name' => 'Fukuoka'),
                array('@type' => 'City', 'name' => 'Kyoto')
            ),
            'medicalSpecialty' => array(
                'General Medicine',
                'Internal Medicine', 
                'ENT (Ear, Nose & Throat)',
                'Dermatology',
                'Gynecology',
                'Cardiology',
                'Orthopedics',
                'Emergency Medicine',
                'Dentistry'
            ),
            'availableLanguage' => array('English', 'Japanese'),
            'additionalProperty' => array(
                array(
                    '@type' => 'PropertyValue',
                    'name' => 'Verification Method',
                    'value' => 'AI-powered English proficiency verification'
                ),
                array(
                    '@type' => 'PropertyValue',
                    'name' => 'Target Audience',
                    'value' => 'International patients, expats, and travelers in Japan'
                )
            ),
            '@id' => $site_url . '#organization'
        );
        
        // Output both schemas
        echo '<script type="application/ld+json">';
        echo wp_json_encode($website_schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
        echo '</script>' . "\n";
        
        echo '<script type="application/ld+json">';
        echo wp_json_encode($organization_schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
        echo '</script>' . "\n";
    }
    
    /**
     * Format business hours for schema.org format
     */
    private function format_business_hours($business_hours) {
        if (empty($business_hours)) {
            return array();
        }
        
        // If business_hours is JSON, decode it
        if (is_string($business_hours)) {
            $hours_data = json_decode($business_hours, true);
        } else {
            $hours_data = $business_hours;
        }
        
        if (!is_array($hours_data)) {
            return array();
        }
        
        $opening_hours = array();
        
        // Map day names
        $day_mapping = array(
            'monday' => 'Mo',
            'tuesday' => 'Tu', 
            'wednesday' => 'We',
            'thursday' => 'Th',
            'friday' => 'Fr',
            'saturday' => 'Sa',
            'sunday' => 'Su'
        );
        
        foreach ($hours_data as $day => $hours) {
            $day_lower = strtolower($day);
            if (isset($day_mapping[$day_lower]) && !empty($hours) && 
                $hours !== 'Closed' && $hours !== 'closed' && 
                $hours !== 'Hours not available') {
                
                $day_code = $day_mapping[$day_lower];
                // Format: "Mo 09:00-17:00"
                $opening_hours[] = $day_code . ' ' . $hours;
            }
        }
        
        return $opening_hours;
    }
}

// Initialize the plugin
function init_healthcare_schema_generator_v2() {
    $healthcare_schema = new HealthcareSchemaGeneratorV2();
    $healthcare_schema->__init();
}
add_action('init', 'init_healthcare_schema_generator_v2');

// Activation hook
register_activation_hook(__FILE__, function() {
    set_transient('healthcare_schema_v2_activated', true, 30);
});

// Add admin notice
add_action('admin_notices', function() {
    if (get_transient('healthcare_schema_v2_activated')) {
        echo '<div class="notice notice-success is-dismissible">';
        echo '<p><strong>Healthcare Schema Generator v2 activated!</strong> Schema.org markup will now be automatically generated with correct ACF field mappings for Care Compass Japan.</p>';
        echo '</div>';
        delete_transient('healthcare_schema_v2_activated');
    }
});

/**
 * Plugin compatibility check
 */
function healthcare_schema_v2_compatibility_check() {
    // Check if ACF is active
    if (!function_exists('get_field')) {
        add_action('admin_notices', function() {
            echo '<div class="notice notice-error">';
            echo '<p><strong>Healthcare Schema Generator v2:</strong> Advanced Custom Fields (ACF) plugin is required but not active.</p>';
            echo '</div>';
        });
    }
    
    // Check if healthcare_provider post type exists
    if (!post_type_exists('healthcare_provider')) {
        add_action('admin_notices', function() {
            echo '<div class="notice notice-warning">';
            echo '<p><strong>Healthcare Schema Generator v2:</strong> The "healthcare_provider" post type was not found. Schema will only work on homepage until this is resolved.</p>';
            echo '</div>';
        });
    }
}
add_action('admin_init', 'healthcare_schema_v2_compatibility_check');

?>