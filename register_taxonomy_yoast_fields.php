<?php
/**
 * Register Yoast SEO REST API fields for taxonomy combination pages
 * Add this to your theme's functions.php or as a separate plugin
 */

// Register Yoast SEO fields for tc_combination post type
add_action('rest_api_init', 'register_taxonomy_yoast_fields');
function register_taxonomy_yoast_fields() {
    
    // Register Yoast SEO title field for tc_combination
    register_rest_field('tc_combination', '_yoast_wpseo_title', array(
        'get_callback' => function($post) {
            return get_post_meta($post['id'], '_yoast_wpseo_title', true);
        },
        'update_callback' => function($value, $post) {
            return update_post_meta($post->ID, '_yoast_wpseo_title', $value);
        },
        'schema' => array(
            'description' => 'Yoast SEO title',
            'type' => 'string',
            'context' => array('view', 'edit'),
        ),
    ));
    
    // Register Yoast SEO meta description field for tc_combination
    register_rest_field('tc_combination', '_yoast_wpseo_metadesc', array(
        'get_callback' => function($post) {
            return get_post_meta($post['id'], '_yoast_wpseo_metadesc', true);
        },
        'update_callback' => function($value, $post) {
            return update_post_meta($post->ID, '_yoast_wpseo_metadesc', $value);
        },
        'schema' => array(
            'description' => 'Yoast SEO meta description',
            'type' => 'string',
            'context' => array('view', 'edit'),
        ),
    ));
    
    // Also register RankMath fields for compatibility
    register_rest_field('tc_combination', '_rank_math_title', array(
        'get_callback' => function($post) {
            return get_post_meta($post['id'], '_rank_math_title', true);
        },
        'update_callback' => function($value, $post) {
            return update_post_meta($post->ID, '_rank_math_title', $value);
        },
        'schema' => array(
            'description' => 'RankMath SEO title',
            'type' => 'string',
            'context' => array('view', 'edit'),
        ),
    ));
    
    register_rest_field('tc_combination', '_rank_math_description', array(
        'get_callback' => function($post) {
            return get_post_meta($post['id'], '_rank_math_description', true);
        },
        'update_callback' => function($value, $post) {
            return update_post_meta($post->ID, '_rank_math_description', $value);
        },
        'schema' => array(
            'description' => 'RankMath meta description', 
            'type' => 'string',
            'context' => array('view', 'edit'),
        ),
    ));
}

// Also register ACF fields for tc_combination if not already done
add_action('acf/init', 'register_taxonomy_acf_fields');
function register_taxonomy_acf_fields() {
    
    if(!function_exists('acf_add_local_field_group')) {
        return;
    }
    
    // Register ACF fields for tc_combination post type
    acf_add_local_field_group(array(
        'key' => 'group_tc_combination',
        'title' => 'Taxonomy Page Fields',
        'fields' => array(
            array(
                'key' => 'field_tc_brief_intro',
                'label' => 'Brief Introduction',
                'name' => 'brief_intro',
                'type' => 'textarea',
                'rows' => 3,
            ),
            array(
                'key' => 'field_tc_full_description',
                'label' => 'Full Description',
                'name' => 'full_description',
                'type' => 'wysiwyg',
                'tabs' => 'all',
                'toolbar' => 'full',
                'media_upload' => 0,
            ),
            array(
                'key' => 'field_tc_seo_title',
                'label' => 'SEO Title',
                'name' => 'seo_title',
                'type' => 'text',
                'instructions' => 'SEO title for meta tags',
            ),
            array(
                'key' => 'field_tc_seo_meta_description',
                'label' => 'SEO Meta Description',
                'name' => 'seo_meta_description',
                'type' => 'textarea',
                'rows' => 2,
                'instructions' => 'Meta description for search engines',
            ),
        ),
        'location' => array(
            array(
                array(
                    'param' => 'post_type',
                    'operator' => '==',
                    'value' => 'tc_combination',
                ),
            ),
        ),
        'menu_order' => 0,
        'position' => 'normal',
        'style' => 'default',
        'label_placement' => 'top',
        'instruction_placement' => 'label',
        'active' => true,
        'show_in_rest' => true,
    ));
}

/**
 * Alternative approach: Hook into save_post to update Yoast fields
 * This ensures Yoast fields are updated when ACF fields are saved
 */
add_action('save_post_tc_combination', 'sync_taxonomy_yoast_fields', 10, 3);
function sync_taxonomy_yoast_fields($post_id, $post, $update) {
    
    // Don't run on autosave
    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
        return;
    }
    
    // Check if ACF fields have SEO data
    $seo_title = get_field('seo_title', $post_id);
    $seo_desc = get_field('seo_meta_description', $post_id);
    
    // If we have ACF SEO fields, update Yoast meta fields
    if ($seo_title) {
        update_post_meta($post_id, '_yoast_wpseo_title', $seo_title);
    }
    
    if ($seo_desc) {
        update_post_meta($post_id, '_yoast_wpseo_metadesc', $seo_desc);
    }
}

/**
 * Debug function to check if Yoast fields are being saved
 * You can call this in WordPress admin to test
 */
function debug_taxonomy_yoast_fields($post_id) {
    $yoast_title = get_post_meta($post_id, '_yoast_wpseo_title', true);
    $yoast_desc = get_post_meta($post_id, '_yoast_wpseo_metadesc', true);
    $acf_title = get_field('seo_title', $post_id);
    $acf_desc = get_field('seo_meta_description', $post_id);
    
    echo "<pre>";
    echo "Post ID: $post_id\n";
    echo "Yoast Title: $yoast_title\n";
    echo "Yoast Description: $yoast_desc\n";
    echo "ACF SEO Title: $acf_title\n";
    echo "ACF SEO Description: $acf_desc\n";
    echo "</pre>";
}