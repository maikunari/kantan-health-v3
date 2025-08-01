# WordPress Taxonomy Combination Pages Implementation Plan
*Blocksy Pro + Greenshift + ACF Pro Integration*

## Project Overview

Create an automated system for generating specialty + location combination pages (e.g., "English Dentist in Yokohama") that leverages existing plugin infrastructure for maximum maintainability and user-friendliness.

**Core Stack Integration:**
- **Blocksy Pro**: Custom page templates and responsive design
- **Greenshift**: Dynamic content blocks and provider listings
- **ACF Pro**: Custom fields and relationship management
- **Yoast SEO**: SEO optimization and schema markup
- **Healthcare Directory**: Existing automation framework integration

## Architecture Overview

### Database Extensions
```sql
-- Extend existing healthcare directory database
CREATE TABLE wp_taxonomy_combination_pages (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    specialty_term_id BIGINT NOT NULL,
    location_term_id BIGINT NOT NULL,
    page_id BIGINT,
    slug VARCHAR(255) UNIQUE,
    status ENUM('pending', 'created', 'ai_generated', 'published') DEFAULT 'pending',
    blocksy_template_applied BOOLEAN DEFAULT FALSE,
    greenshift_pattern_applied BOOLEAN DEFAULT FALSE,
    acf_fields_populated BOOLEAN DEFAULT FALSE,
    ai_description_generated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (specialty_term_id) REFERENCES wp_terms(term_id),
    FOREIGN KEY (location_term_id) REFERENCES wp_terms(term_id),
    FOREIGN KEY (page_id) REFERENCES wp_posts(ID),
    INDEX idx_terms (specialty_term_id, location_term_id),
    INDEX idx_status (status)
);
```

### File Structure
```
/wordpress-taxonomy-automation/
├── combination_page_manager.py           # Main automation script
├── blocksy_integration.py                # Blocksy Pro template management
├── greenshift_integration.py             # Greenshift block patterns
├── acf_field_manager.py                  # ACF Pro field automation
├── ai_combination_content.py             # Claude AI content generation
├── yoast_seo_automation.py               # Yoast SEO field management
├── wordpress_plugin/                     # WordPress plugin files
│   ├── healthcare-taxonomy-automation.php
│   ├── admin/
│   │   ├── combination-pages-admin.php
│   │   ├── batch-creation-interface.php
│   │   └── assets/
│   ├── includes/
│   │   ├── acf-field-groups.php
│   │   ├── taxonomy-hooks.php
│   │   ├── blocksy-templates.php
│   │   └── greenshift-patterns.php
│   └── templates/
│       ├── combination-page-blocksy.php
│       └── greenshift-patterns.json
└── web-interface/                        # React components
    ├── TaxonomyCombinations/
    │   ├── CombinationManager.tsx
    │   ├── BatchCreationModal.tsx
    │   ├── GreenshiftPreview.tsx
    │   └── SEOOptimization.tsx
    └── api-extensions/
        └── combination-endpoints.py
```

## Phase 1: ACF Pro Foundation Setup

### 1.1 ACF Field Groups Creation
**File**: `wordpress_plugin/includes/acf-field-groups.php`

```php
function register_combination_page_fields() {
    if (function_exists('acf_add_local_field_group')) {
        
        // Main Combination Fields
        acf_add_local_field_group([
            'key' => 'group_combination_main',
            'title' => 'Combination Page Settings',
            'fields' => [
                [
                    'key' => 'field_specialty_term',
                    'label' => 'Specialty',
                    'name' => 'combination_specialty',
                    'type' => 'taxonomy',
                    'taxonomy' => 'specialty',
                    'field_type' => 'select',
                    'return_format' => 'object',
                ],
                [
                    'key' => 'field_location_term',
                    'label' => 'Location', 
                    'name' => 'combination_location',
                    'type' => 'taxonomy',
                    'taxonomy' => 'location',
                    'field_type' => 'select',
                    'return_format' => 'object',
                ],
                [
                    'key' => 'field_provider_count',
                    'label' => 'Provider Count',
                    'name' => 'provider_count',
                    'type' => 'number',
                    'readonly' => 1,
                ],
            ],
            'location' => [
                [
                    [
                        'param' => 'post_template',
                        'operator' => '==',
                        'value' => 'combination-page-template.php',
                    ],
                ],
            ],
        ]);

        // SEO Enhancement Fields
        acf_add_local_field_group([
            'key' => 'group_combination_seo',
            'title' => 'Combination SEO Settings',
            'fields' => [
                [
                    'key' => 'field_custom_title',
                    'label' => 'Custom Page Title',
                    'name' => 'custom_page_title',
                    'type' => 'text',
                    'placeholder' => 'English {specialty} in {location}',
                ],
                [
                    'key' => 'field_custom_intro',
                    'label' => 'Custom Introduction',
                    'name' => 'custom_introduction',
                    'type' => 'wysiwyg',
                    'toolbar' => 'basic',
                ],
                [
                    'key' => 'field_local_info',
                    'label' => 'Local Healthcare Information',
                    'name' => 'local_healthcare_info',
                    'type' => 'wysiwyg',
                ],
                [
                    'key' => 'field_ai_generated_content',
                    'label' => 'AI Generated Description',
                    'name' => 'ai_generated_content',
                    'type' => 'wysiwyg',
                    'readonly' => 1,
                ],
            ],
            'location' => [
                [
                    [
                        'param' => 'post_template',
                        'operator' => '==', 
                        'value' => 'combination-page-template.php',
                    ],
                ],
            ],
        ]);

        // Provider Display Settings
        acf_add_local_field_group([
            'key' => 'group_combination_display',
            'title' => 'Provider Display Settings',
            'fields' => [
                [
                    'key' => 'field_show_map',
                    'label' => 'Show Location Map',
                    'name' => 'show_location_map',
                    'type' => 'true_false',
                    'default_value' => 1,
                ],
                [
                    'key' => 'field_providers_per_page',
                    'label' => 'Providers Per Page',
                    'name' => 'providers_per_page',
                    'type' => 'number',
                    'default_value' => 12,
                ],
                [
                    'key' => 'field_display_style',
                    'label' => 'Provider Display Style',
                    'name' => 'provider_display_style',
                    'type' => 'select',
                    'choices' => [
                        'grid' => 'Grid Layout',
                        'list' => 'List Layout',
                        'cards' => 'Card Layout',
                    ],
                    'default_value' => 'cards',
                ],
            ],
            'location' => [
                [
                    [
                        'param' => 'post_template',
                        'operator' => '==',
                        'value' => 'combination-page-template.php',
                    ],
                ],
            ],
        ]);
    }
}
add_action('acf/init', 'register_combination_page_fields');
```

### 1.2 ACF Field Management Class
**File**: `acf_field_manager.py`

```python
class ACFFieldManager:
    def __init__(self):
        self.wp_api = WordPressAPI()
    
    def populate_combination_fields(self, page_id, specialty_term, location_term, provider_count=0):
        """Populate ACF fields for a combination page"""
        fields = {
            'combination_specialty': specialty_term.term_id,
            'combination_location': location_term.term_id,
            'provider_count': provider_count,
            'custom_page_title': f"English {specialty_term.name} in {location_term.name}",
            'show_location_map': True,
            'providers_per_page': 12,
            'provider_display_style': 'cards'
        }
        
        for field_name, value in fields.items():
            self.wp_api.update_acf_field(page_id, field_name, value)
    
    def update_ai_content(self, page_id, ai_description):
        """Update AI generated content field"""
        self.wp_api.update_acf_field(page_id, 'ai_generated_content', ai_description)
    
    def get_combination_data(self, page_id):
        """Retrieve combination data from ACF fields"""
        return {
            'specialty': self.wp_api.get_acf_field(page_id, 'combination_specialty'),
            'location': self.wp_api.get_acf_field(page_id, 'combination_location'),
            'provider_count': self.wp_api.get_acf_field(page_id, 'provider_count'),
            'display_style': self.wp_api.get_acf_field(page_id, 'provider_display_style')
        }
```

## Phase 2: Blocksy Pro Template System

### 2.1 Blocksy Template Creation
**File**: `wordpress_plugin/includes/blocksy-templates.php`

```php
function register_combination_page_template() {
    // Register custom page template in Blocksy
    add_filter('blocksy:general:page-templates', function($templates) {
        $templates['combination-page-template.php'] = [
            'label' => 'Combination Page Template',
            'thumbnail' => plugins_url('assets/combination-template-thumb.png', __FILE__),
        ];
        return $templates;
    });
}
add_action('init', 'register_combination_page_template');

function apply_blocksy_template_to_combination($page_id, $template_name = 'combination-page-template') {
    // Apply Blocksy template
    update_post_meta($page_id, '_wp_page_template', $template_name . '.php');
    
    // Set Blocksy specific settings
    update_post_meta($page_id, 'blocksy_page_header_type', 'type-1');
    update_post_meta($page_id, 'blocksy_page_breadcrumbs', 'enabled');
    update_post_meta($page_id, 'blocksy_page_sidebar', 'none');
    
    // Apply custom Blocksy styling
    $blocksy_settings = [
        'hero_section' => [
            'enabled' => true,
            'background_type' => 'gradient',
            'text_color' => '#ffffff'
        ],
        'content_layout' => [
            'container_type' => 'normal',
            'sidebar_position' => 'none'
        ],
        'seo_settings' => [
            'breadcrumbs' => true,
            'schema_markup' => 'medical_business'
        ]
    ];
    
    update_post_meta($page_id, 'blocksy_combination_settings', json_encode($blocksy_settings));
}
```

### 2.2 Blocksy Integration Class
**File**: `blocksy_integration.py`

```python
class BlocksyIntegration:
    def __init__(self):
        self.wp_api = WordPressAPI()
    
    def apply_combination_template(self, page_id, specialty, location):
        """Apply Blocksy template and settings to combination page"""
        
        # Set page template
        self.wp_api.update_post_meta(page_id, '_wp_page_template', 'combination-page-template.php')
        
        # Configure Blocksy settings
        blocksy_settings = {
            'page_header_type': 'type-1',
            'breadcrumbs': 'enabled',
            'sidebar': 'none',
            'hero_section': {
                'enabled': True,
                'title': f"English {specialty} in {location}",
                'subtitle': f"Find quality {specialty.lower()} services with English support",
                'background_type': 'gradient'
            },
            'content_layout': {
                'container_type': 'normal',
                'max_width': '1200px'
            }
        }
        
        # Apply settings
        for key, value in blocksy_settings.items():
            self.wp_api.update_post_meta(page_id, f'blocksy_{key}', json.dumps(value) if isinstance(value, dict) else value)
    
    def configure_responsive_design(self, page_id, display_style='cards'):
        """Configure Blocksy responsive settings"""
        responsive_config = {
            'desktop': {
                'columns': 3 if display_style == 'cards' else 1,
                'spacing': '30px'
            },
            'tablet': {
                'columns': 2 if display_style == 'cards' else 1,
                'spacing': '20px'
            },
            'mobile': {
                'columns': 1,
                'spacing': '15px'
            }
        }
        
        self.wp_api.update_post_meta(page_id, 'blocksy_responsive_config', json.dumps(responsive_config))
```

## Phase 3: Greenshift Dynamic Content System

### 3.1 Greenshift Block Patterns
**File**: `wordpress_plugin/includes/greenshift-patterns.php`

```php
function register_combination_greenshift_patterns() {
    if (function_exists('greenshift_register_pattern')) {
        
        // Main combination page pattern
        greenshift_register_pattern([
            'slug' => 'combination-page-layout',
            'title' => 'Combination Page Layout',
            'description' => 'Complete layout for specialty/location combination pages',
            'categories' => ['healthcare', 'combination-pages'],
            'content' => '
                <!-- wp:greenshift-blocks/container -->
                <div class="wp-block-greenshift-blocks-container">
                    
                    <!-- Hero Section with Dynamic Title -->
                    <!-- wp:greenshift-blocks/heading {"dynamicContent":{"field":"custom_page_title","source":"acf"}} -->
                    <h1 class="wp-block-greenshift-blocks-heading">English {specialty} in {location}</h1>
                    <!-- /wp:greenshift-blocks/heading -->
                    
                    <!-- Dynamic Introduction -->
                    <!-- wp:greenshift-blocks/text {"dynamicContent":{"field":"custom_introduction","source":"acf"}} -->
                    <p>Find quality {specialty} services with English language support in {location}.</p>
                    <!-- /wp:greenshift-blocks/text -->
                    
                    <!-- Provider Count Display -->
                    <!-- wp:greenshift-blocks/counter {"dynamicContent":{"field":"provider_count","source":"acf"}} -->
                    <div class="wp-block-greenshift-blocks-counter">
                        <span class="counter-number">0</span>
                        <span class="counter-label">Verified Providers</span>
                    </div>
                    <!-- /wp:greenshift-blocks/counter -->
                    
                    <!-- AI Generated Content Section -->
                    <!-- wp:greenshift-blocks/accordion -->
                    <div class="wp-block-greenshift-blocks-accordion">
                        <div class="accordion-item">
                            <h3>About {specialty} Services in {location}</h3>
                            <!-- wp:greenshift-blocks/text {"dynamicContent":{"field":"ai_generated_content","source":"acf"}} -->
                            <div class="ai-generated-content"></div>
                            <!-- /wp:greenshift-blocks/text -->
                        </div>
                    </div>
                    <!-- /wp:greenshift-blocks/accordion -->
                    
                    <!-- Dynamic Provider Query -->
                    <!-- wp:greenshift-blocks/query-loop {"query":{"post_type":"provider","meta_query":[{"key":"specialty","value":"{{specialty}}","compare":"="},{"key":"location","value":"{{location}}","compare":"="}]}} -->
                    <div class="wp-block-greenshift-blocks-query-loop provider-grid">
                        <!-- wp:greenshift-blocks/query-card -->
                        <div class="provider-card">
                            <!-- wp:greenshift-blocks/post-title {"isLink":true} /-->
                            <!-- wp:greenshift-blocks/post-excerpt /-->
                            <!-- wp:greenshift-blocks/custom-field {"field":"address"} /-->
                            <!-- wp:greenshift-blocks/custom-field {"field":"phone"} /-->
                            <!-- wp:greenshift-blocks/button {"text":"View Details","link":"{{permalink}}"} /-->
                        </div>
                        <!-- /wp:greenshift-blocks/query-card -->
                    </div>
                    <!-- /wp:greenshift-blocks/query-loop -->
                    
                    <!-- Conditional Map Display -->
                    <!-- wp:greenshift-blocks/conditional {"condition":{"field":"show_location_map","source":"acf","operator":"==","value":"1"}} -->
                    <div class="location-map-section">
                        <!-- wp:greenshift-blocks/map {"location":"{{location}}","zoom":12} /-->
                    </div>
                    <!-- /wp:greenshift-blocks/conditional -->
                    
                </div>
                <!-- /wp:greenshift-blocks/container -->
            '
        ]);
        
        // Provider card pattern
        greenshift_register_pattern([
            'slug' => 'provider-card-layout',
            'title' => 'Provider Card Layout',
            'description' => 'Individual provider card for combination pages',
            'categories' => ['healthcare', 'provider-cards'],
            'content' => '
                <!-- wp:greenshift-blocks/container {"className":"provider-card"} -->
                <div class="wp-block-greenshift-blocks-container provider-card">
                    <!-- wp:greenshift-blocks/image {"dynamicContent":{"field":"featured_image"}} /-->
                    <!-- wp:greenshift-blocks/heading {"level":3,"dynamicContent":{"field":"post_title"}} /-->
                    <!-- wp:greenshift-blocks/text {"dynamicContent":{"field":"specialty","source":"taxonomy"}} /-->
                    <!-- wp:greenshift-blocks/text {"dynamicContent":{"field":"address","source":"acf"}} /-->
                    <!-- wp:greenshift-blocks/rating {"dynamicContent":{"field":"rating","source":"acf"}} /-->
                    <!-- wp:greenshift-blocks/button {"text":"View Details","dynamicLink":{"field":"permalink"}} /-->
                </div>
                <!-- /wp:greenshift-blocks/container -->
            '
        ]);
    }
}
add_action('init', 'register_combination_greenshift_patterns');
```

### 3.2 Greenshift Integration Class
**File**: `greenshift_integration.py`

```python
class GreenshiftIntegration:
    def __init__(self):
        self.wp_api = WordPressAPI()
    
    def apply_combination_pattern(self, page_id, specialty, location, display_style='cards'):
        """Apply Greenshift block pattern to combination page"""
        
        # Get the appropriate pattern based on display style
        pattern_content = self.get_pattern_content(specialty, location, display_style)
        
        # Update page content with Greenshift blocks
        self.wp_api.update_post_content(page_id, pattern_content)
        
        # Configure dynamic query parameters
        self.configure_dynamic_query(page_id, specialty, location)
    
    def get_pattern_content(self, specialty, location, display_style):
        """Generate Greenshift pattern content with dynamic values"""
        
        base_pattern = self.load_pattern_template('combination-page-layout')
        
        # Replace placeholders with actual values
        pattern_content = base_pattern.replace('{specialty}', specialty)
        pattern_content = pattern_content.replace('{location}', location)
        
        # Adjust layout based on display style
        if display_style == 'grid':
            pattern_content = pattern_content.replace('provider-grid', 'provider-grid grid-layout')
        elif display_style == 'list':
            pattern_content = pattern_content.replace('provider-grid', 'provider-list list-layout')
        
        return pattern_content
    
    def configure_dynamic_query(self, page_id, specialty_term_id, location_term_id):
        """Configure Greenshift dynamic query for providers"""
        
        query_config = {
            'post_type': 'provider',
            'posts_per_page': 12,
            'meta_query': [
                {
                    'key': 'specialty',
                    'value': specialty_term_id,
                    'compare': '='
                },
                {
                    'key': 'location', 
                    'value': location_term_id,
                    'compare': '='
                }
            ],
            'orderby': 'title',
            'order': 'ASC'
        }
        
        # Store query configuration for Greenshift
        self.wp_api.update_post_meta(page_id, 'greenshift_query_config', json.dumps(query_config))
    
    def update_provider_count(self, page_id, specialty_term_id, location_term_id):
        """Update provider count for dynamic display"""
        
        # Query database for actual provider count
        count = self.get_provider_count(specialty_term_id, location_term_id)
        
        # Update ACF field for Greenshift counter block
        self.wp_api.update_acf_field(page_id, 'provider_count', count)
        
        return count
    
    def get_provider_count(self, specialty_term_id, location_term_id):
        """Get actual provider count from database"""
        # This would integrate with your existing healthcare directory database
        from postgres_integration import Provider, get_db_session
        
        session = get_db_session()
        count = session.query(Provider).filter(
            Provider.specialty_id == specialty_term_id,
            Provider.location_id == location_term_id,
            Provider.status == 'published'
        ).count()
        session.close()
        
        return count
```

## Phase 4: AI Content Generation Integration

### 4.1 Combination Content Generator
**File**: `ai_combination_content.py`

```python
class CombinationContentGenerator:
    def __init__(self):
        self.claude_client = ClaudeClient()
        self.acf_manager = ACFFieldManager()
        
    def generate_combination_description(self, specialty, location, provider_count=0, existing_providers=None):
        """Generate AI content for specialty/location combination"""
        
        # Enhanced prompt with provider context
        provider_context = ""
        if existing_providers and len(existing_providers) > 0:
            provider_names = [p.get('name', 'Unknown') for p in existing_providers[:3]]
            provider_context = f"\n\nVerified providers in this area include: {', '.join(provider_names)}."
        
        prompt = f"""
        Create comprehensive, SEO-optimized content for English-speaking {specialty} services in {location}, Japan.
        
        Content should include:
        
        **Overview Section (100-150 words):**
        - Introduction to {specialty} services available in {location}
        - Benefits for international patients and English speakers
        - Why {location} is a good choice for {specialty} care
        
        **What to Expect Section (150-200 words):**
        - Typical {specialty} procedures and treatments available
        - English language support and communication
        - Cultural considerations and patient experience
        - Insurance and payment options for international patients
        
        **Local Healthcare Navigation (100-150 words):**
        - How to book appointments in {location}
        - Transportation and accessibility information
        - Emergency contact information
        - Follow-up care and prescription access
        
        **Quality and Standards (50-100 words):**
        - Japanese healthcare quality standards
        - International certifications and training
        - Technology and equipment standards
        
        {provider_context}
        {f"We currently have {provider_count} verified {specialty.lower()} providers in {location}." if provider_count > 0 else ""}
        
        Target audience: International residents, expats, and tourists in Japan
        Tone: Professional, reassuring, informative, helpful
        SEO focus: Natural keyword integration for "{specialty} {location}"
        
        Format as clean HTML with appropriate headings (h2, h3) and semantic markup.
        """
        
        return self.claude_client.generate_content(prompt)
    
    def generate_seo_metadata(self, specialty, location, provider_count=0):
        """Generate SEO-optimized metadata"""
        
        prompt = f"""
        Create SEO metadata for English-speaking {specialty} services in {location}, Japan.
        
        Generate:
        1. SEO Title (55-60 characters): Include "English", specialty, location
        2. Meta Description (150-160 characters): Compelling, includes key benefits
        3. Focus Keywords: Primary and 2-3 secondary keywords
        4. Schema Markup suggestions for local medical business
        
        Target: International patients seeking {specialty} care in {location}
        {f"Highlight: {provider_count} verified providers available" if provider_count > 0 else ""}
        
        Return as JSON format.
        """
        
        response = self.claude_client.generate_content(prompt)
        return json.loads(response)
    
    def process_combination_batch(self, combinations, batch_size=2):
        """Process multiple combinations using mega-batch approach"""
        
        # Integrate with existing mega-batch processor
        from claude_mega_batch_processor import MegaBatchProcessor
        
        processor = MegaBatchProcessor()
        
        for i in range(0, len(combinations), batch_size):
            batch = combinations[i:i + batch_size]
            
            # Prepare batch prompts
            batch_prompts = []
            for combo in batch:
                content_prompt = self.build_combination_prompt(combo)
                batch_prompts.append({
                    'combination_id': combo['id'],
                    'page_id': combo['page_id'],
                    'prompt': content_prompt
                })
            
            # Process batch
            results = processor.process_batch(batch_prompts)
            
            # Update pages with results
            for result in results:
                if result['success']:
                    self.acf_manager.update_ai_content(
                        result['page_id'], 
                        result['generated_content']
                    )
                    
                    # Update status
                    self.update_combination_status(
                        result['combination_id'], 
                        'ai_generated'
                    )
```

### 4.2 Yoast SEO Integration
**File**: `yoast_seo_automation.py`

```python
class YoastSEOIntegration:
    def __init__(self):
        self.wp_api = WordPressAPI()
    
    def set_yoast_fields(self, page_id, specialty, location, seo_metadata):
        """Set Yoast SEO fields for combination page"""
        
        yoast_fields = {
            '_yoast_wpseo_title': seo_metadata.get('seo_title', f"English {specialty} in {location} - Quality Healthcare"),
            '_yoast_wpseo_metadesc': seo_metadata.get('meta_description', f"Find English-speaking {specialty} in {location}. Quality healthcare with international patient support."),
            '_yoast_wpseo_focuskw': seo_metadata.get('focus_keyword', f"{specialty} {location}"),
            '_yoast_wpseo_canonical': f"https://yoursite.com/english-{specialty.lower()}-{location.lower()}/",
            '_yoast_wpseo_opengraph-title': seo_metadata.get('og_title', seo_metadata.get('seo_title')),
            '_yoast_wpseo_opengraph-description': seo_metadata.get('og_description', seo_metadata.get('meta_description')),
            '_yoast_wpseo_twitter-title': seo_metadata.get('twitter_title', seo_metadata.get('seo_title')),
            '_yoast_wpseo_twitter-description': seo_metadata.get('twitter_description', seo_metadata.get('meta_description')),
        }
        
        # Set schema markup
        schema_data = {
            '@context': 'https://schema.org',
            '@type': 'MedicalBusiness',
            'name': f"English {specialty} in {location}",
            'description': seo_metadata.get('meta_description'),
            'address': {
                '@type': 'PostalAddress',
                'addressLocality': location,
                'addressCountry': 'Japan'
            },
            'medicalSpecialty': specialty,
            'availableLanguage': ['English', 'Japanese']
        }
        
        yoast_fields['_yoast_wpseo_schema_page_type'] = 'MedicalBusiness'
        yoast_fields['_yoast_wpseo_schema_page_type_custom'] = json.dumps(schema_data)
        
        # Apply all Yoast fields
        for field, value in yoast_fields.items():
            self.wp_api.update_post_meta(page_id, field, value)
    
    def set_breadcrumbs(self, page_id, specialty, location):
        """Configure Yoast breadcrumb navigation"""
        
        breadcrumb_config = [
            {'text': 'Home', 'url': '/'},
            {'text': 'Healthcare Directory', 'url': '/providers/'},
            {'text': specialty, 'url': f'/specialty/{specialty.lower()}/'},
            {'text': location, 'url': f'/location/{location.lower()}/'},
            {'text': f"English {specialty} in {location}", 'url': ''}
        ]
        
        self.wp_api.update_post_meta(page_id, '_yoast_wpseo_breadcrumbs_override', json.dumps(breadcrumb_config))
```

## Phase 5: Main Automation System

### 5.1 Combination Page Manager
**File**: `combination_page_manager.py`

```python
class CombinationPageManager:
    def __init__(self):
        self.wp_api = WordPressAPI()
        self.acf_manager = ACFFieldManager()
        self.blocksy_integration = BlocksyIntegration()
        self.greenshift_integration = GreenshiftIntegration()
        self.content_generator = CombinationContentGenerator()
        self.yoast_integration = YoastSEOIntegration()
        self.db = PostgresIntegration()
        
    def create_combination_page(self, specialty_term, location_term, auto_generate_content=True):
        """Create a complete combination page with all integrations"""
        
        try:
            # 1. Create WordPress page
            page_data = {
                'title': f"English {specialty_term.name} in {location_term.name}",
                'slug': f"english-{specialty_term.slug}-{location_term.slug}",
                'status': 'draft',
                'type': 'page'
            }
            
            page_id = self.wp_api.create_page(page_data)
            
            # 2. Apply Blocksy template
            self.blocksy_integration.apply_combination_template(
                page_id, specialty_term.name, location_term.name
            )
            
            # 3. Populate ACF fields
            provider_count = self.get_provider_count(specialty_term.term_id, location_term.term_id)
            self.acf_manager.populate_combination_fields(
                page_id, specialty_term, location_term, provider_count
            )
            
            # 4. Apply Greenshift pattern
            self.greenshift_integration.apply_combination_pattern(
                page_id, specialty_term.name, location_term.name
            )
            
            # 5. Generate AI content
            if auto_generate_content:
                ai_content = self.content_generator.generate_combination_description(
                    specialty_term.name, location_term.name, provider_count
                )
                self.acf_manager.update_ai_content(page_id, ai_content)
                
                # Generate and apply SEO metadata
                seo_metadata = self.content_generator.generate_seo_metadata(
                    specialty_term.name, location_term.name, provider_count
                )
                self.yoast_integration.set_yoast_fields(
                    page_id, specialty_term.name, location_term.name, seo_metadata
                )
            
            # 6. Update tracking database
            self.track_combination_page(
                specialty_term.term_id, location_term.term_id, page_id, 
                'ai_generated' if auto_generate_content else 'created'
            )
            
            # 7. Log activity
            from activity_logger import activity_logger
            activity_logger.log_activity(
                activity_type='create_combination_page',
                activity_category='taxonomy_combinations',
                description=f"Created combination page: {specialty_term.name} in {location_term.name}",
                details={
                    'specialty': specialty_term.name,
                    'location': location_term.name,
                    'page_id': page_id,
                    'provider_count': provider_count,
                    'ai_content_generated': auto_generate_content
                },
                status='success'
            )
            
            return {
                'success': True,
                'page_id': page_id,
                'slug': page_data['slug'],
                'url': f"https://yoursite.com/{page_data['slug']}/"
            }
            
        except Exception as e:
            logger.error(f"Failed to create combination page: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def scan_missing_combinations(self):
        """Scan for missing specialty/location combinations"""
        
        # Get all specialty and location terms
        specialties = self.wp_api.get_taxonomy_terms('specialty')
        locations = self.wp_api.get_taxonomy_terms('location')
        
        # Get existing combinations from database
        existing_combinations = self.get_existing_combinations()
        existing_pairs = [(c['specialty_term_id'], c['location_term_id']) for c in existing_combinations]
        
        missing_combinations = []
        
        for specialty in specialties:
            for location in locations:
                if (specialty.term_id, location.term_id) not in existing_pairs:
                    # Check if we have providers for this combination
                    provider_count = self.get_provider_count(specialty.term_id, location.term_id)
                    
                    if provider_count > 0:  # Only create if we have providers
                        missing_combinations.append({
                            'specialty': specialty,
                            'location': location,
                            'provider_count': provider_count
                        })
        
        return missing_combinations
    
    def batch_create_combinations(self, combinations_to_create, auto_ai_content=True):
        """Create multiple combination pages in batch"""
        
        results = []
        
        for combo in combinations_to_create:
            result = self.create_combination_page(
                combo['specialty'], 
                combo['location'],
                auto_ai_content
            )
            results.append(result)
            
            # Small delay to avoid overwhelming APIs
            time.sleep(1)
        
        return results
    
    def update_provider_counts(self):
        """Update provider counts for all existing combination pages"""
        
        existing_combinations = self.get_existing_combinations()
        
        for combo in existing_combinations:
            if combo['page_id']:
                provider_count = self.get_provider_count(
                    combo['specialty_term_id'], 
                    combo['location_term_id']
                )
                
                # Update ACF field
                self.acf_manager.populate_combination_fields(
                    combo['page_id'], None, None, provider_count
                )
                
                # Update Greenshift counter
                self.greenshift_integration.update_provider_count(
                    combo['page_id'], 
                    combo['specialty_term_id'], 
                    combo['location_term_id']
                )
    
    def get_provider_count(self, specialty_term_id, location_term_id):
        """Get provider count for specialty/location combination"""
        # Integrate with existing healthcare directory database
        session = self.db.get_session()
        
        count = session.query(Provider).filter(
            Provider.specialty_id == specialty_term_id,
            Provider.location_id == location_term_id,
            Provider.status.in_(['published', 'approved'])
        ).count()
        
        session.close()
        return count
    
    def track_combination_page(self, specialty_term_id, location_term_id, page_id, status):
        """Track combination page in database"""
        
        session = self.db.get_session()
        
        # Check if combination already exists
        existing = session.execute(text("""
            SELECT id FROM wp_taxonomy_combination_pages 
            WHERE specialty_term_id = :specialty_id AND location_term_id = :location_id
        """), {
            'specialty_id': specialty_term_id,
            'location_id': location_term_id
        }).fetchone()
        
        if existing:
            # Update existing record
            session.execute(text("""
                UPDATE wp_taxonomy_combination_pages 
                SET page_id = :page_id, status = :status, updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """), {
                'page_id': page_id,
                'status': status,
                'id': existing.id
            })
        else:
            # Insert new record
            session.execute(text("""
                INSERT INTO wp_taxonomy_combination_pages 
                (specialty_term_id, location_term_id, page_id, status, created_at, updated_at)
                VALUES (:specialty_id, :location_id, :page_id, :status, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """), {
                'specialty_id': specialty_term_id,
                'location_id': location_term_id,
                'page_id': page_id,
                'status': status
            })
        
        session.commit()
        session.close()
    
    def get_existing_combinations(self):
        """Get all existing combination pages from database"""
        
        session = self.db.get_session()
        
        result = session.execute(text("""
            SELECT tcp.*, 
                   s.name as specialty_name, s.slug as specialty_slug,
                   l.name as location_name, l.slug as location_slug
            FROM wp_taxonomy_combination_pages tcp
            LEFT JOIN wp_terms s ON tcp.specialty_term_id = s.term_id
            LEFT JOIN wp_terms l ON tcp.location_term_id = l.term_id
            ORDER BY tcp.created_at DESC
        """)).fetchall()
        
        combinations = []
        for row in result:
            combinations.append({
                'id': row.id,
                'specialty_term_id': row.specialty_term_id,
                'location_term_id': row.location_term_id,
                'page_id': row.page_id,
                'status': row.status,
                'specialty_name': row.specialty_name,
                'specialty_slug': row.specialty_slug,
                'location_name': row.location_name,
                'location_slug': row.location_slug,
                'created_at': row.created_at
            })
        
        session.close()
        return combinations
```

## Phase 6: WordPress Plugin Implementation

### 6.1 Main Plugin File
**File**: `wordpress_plugin/healthcare-taxonomy-automation.php`

```php
<?php
/**
 * Plugin Name: Healthcare Taxonomy Automation
 * Description: Automated creation and management of specialty/location combination pages
 * Version: 1.0.0
 * Author: Healthcare Directory Team
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Define plugin constants
define('HTA_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('HTA_PLUGIN_URL', plugin_dir_url(__FILE__));

// Include required files
require_once HTA_PLUGIN_DIR . 'includes/acf-field-groups.php';
require_once HTA_PLUGIN_DIR . 'includes/taxonomy-hooks.php';
require_once HTA_PLUGIN_DIR . 'includes/blocksy-templates.php';
require_once HTA_PLUGIN_DIR . 'includes/greenshift-patterns.php';
require_once HTA_PLUGIN_DIR . 'admin/combination-pages-admin.php';

// Initialize plugin
class HealthcareTaxonomyAutomation {
    
    public function __construct() {
        add_action('init', [$this, 'init']);
        add_action('admin_menu', [$this, 'add_admin_menu']);
        register_activation_hook(__FILE__, [$this, 'activate']);
        register_deactivation_hook(__FILE__, [$this, 'deactivate']);
    }
    
    public function init() {
        // Initialize components
        new TaxonomyHooks();
        new CombinationPagesAdmin();
        
        // Register REST API endpoints
        add_action('rest_api_init', [$this, 'register_rest_routes']);
    }
    
    public function add_admin_menu() {
        add_menu_page(
            'Combination Pages',
            'Combination Pages',
            'manage_options',
            'combination-pages',
            [$this, 'admin_page'],
            'dashicons-networking',
            30
        );
        
        add_submenu_page(
            'combination-pages',
            'Batch Creation',
            'Batch Creation',
            'manage_options',
            'combination-batch',
            [$this, 'batch_creation_page']
        );
    }
    
    public function admin_page() {
        include HTA_PLUGIN_DIR . 'admin/combination-pages-admin.php';
    }
    
    public function batch_creation_page() {
        include HTA_PLUGIN_DIR . 'admin/batch-creation-interface.php';
    }
    
    public function register_rest_routes() {
        register_rest_route('healthcare/v1', '/combinations', [
            'methods' => 'GET',
            'callback' => [$this, 'get_combinations'],
            'permission_callback' => '__return_true'
        ]);
        
        register_rest_route('healthcare/v1', '/combinations/scan', [
            'methods' => 'POST',
            'callback' => [$this, 'scan_missing_combinations'],
            'permission_callback' => 'current_user_can_manage_options'
        ]);
        
        register_rest_route('healthcare/v1', '/combinations/create', [
            'methods' => 'POST',
            'callback' => [$this, 'create_combination_batch'],
            'permission_callback' => 'current_user_can_manage_options'
        ]);
    }
    
    public function get_combinations($request) {
        // Return existing combinations data
        global $wpdb;
        
        $results = $wpdb->get_results("
            SELECT tcp.*, 
                   s.name as specialty_name, s.slug as specialty_slug,
                   l.name as location_name, l.slug as location_slug,
                   p.post_title, p.post_status, p.post_date
            FROM {$wpdb->prefix}taxonomy_combination_pages tcp
            LEFT JOIN {$wpdb->terms} s ON tcp.specialty_term_id = s.term_id
            LEFT JOIN {$wpdb->terms} l ON tcp.location_term_id = l.term_id
            LEFT JOIN {$wpdb->posts} p ON tcp.page_id = p.ID
            ORDER BY tcp.created_at DESC
        ");
        
        return rest_ensure_response($results);
    }
    
    public function scan_missing_combinations($request) {
        // Trigger Python script to scan for missing combinations
        $output = shell_exec('cd ' . ABSPATH . '../ && python3 combination_page_manager.py --scan-missing 2>&1');
        
        return rest_ensure_response([
            'success' => true,
            'output' => $output
        ]);
    }
    
    public function create_combination_batch($request) {
        $combinations = $request->get_param('combinations');
        $auto_ai_content = $request->get_param('auto_ai_content', true);
        
        // Trigger Python script for batch creation
        $command = sprintf(
            'cd %s/../ && python3 combination_page_manager.py --batch-create "%s" --auto-ai=%s 2>&1',
            ABSPATH,
            base64_encode(json_encode($combinations)),
            $auto_ai_content ? 'true' : 'false'
        );
        
        $output = shell_exec($command);
        
        return rest_ensure_response([
            'success' => true,
            'output' => $output
        ]);
    }
    
    public function activate() {
        // Create database table
        global $wpdb;
        
        $table_name = $wpdb->prefix . 'taxonomy_combination_pages';
        
        $charset_collate = $wpdb->get_charset_collate();
        
        $sql = "CREATE TABLE $table_name (
            id bigint(20) NOT NULL AUTO_INCREMENT,
            specialty_term_id bigint(20) NOT NULL,
            location_term_id bigint(20) NOT NULL,
            page_id bigint(20) DEFAULT NULL,
            slug varchar(255) DEFAULT NULL,
            status enum('pending','created','ai_generated','published') DEFAULT 'pending',
            blocksy_template_applied tinyint(1) DEFAULT 0,
            greenshift_pattern_applied tinyint(1) DEFAULT 0,
            acf_fields_populated tinyint(1) DEFAULT 0,
            ai_description_generated tinyint(1) DEFAULT 0,
            created_at timestamp DEFAULT CURRENT_TIMESTAMP,
            updated_at timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            UNIQUE KEY unique_combination (specialty_term_id, location_term_id),
            KEY idx_status (status),
            KEY idx_page_id (page_id)
        ) $charset_collate;";
        
        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql);
    }
    
    public function deactivate() {
        // Cleanup if needed
    }
}

// Initialize plugin
new HealthcareTaxonomyAutomation();

// Helper function for other files
function current_user_can_manage_options() {
    return current_user_can('manage_options');
}
```

### 6.2 Taxonomy Hooks System
**File**: `wordpress_plugin/includes/taxonomy-hooks.php`

```php
<?php

class TaxonomyHooks {
    
    public function __construct() {
        add_action('created_term', [$this, 'handle_new_term'], 10, 3);
        add_action('edited_term', [$this, 'handle_updated_term'], 10, 3);
        add_action('delete_term', [$this, 'handle_deleted_term'], 10, 4);
    }
    
    public function handle_new_term($term_id, $tt_id, $taxonomy) {
        if (!in_array($taxonomy, ['specialty', 'location'])) {
            return;
        }
        
        // Trigger combination page generation for new term
        $this->trigger_combination_generation($term_id, $taxonomy);
    }
    
    public function handle_updated_term($term_id, $tt_id, $taxonomy) {
        if (!in_array($taxonomy, ['specialty', 'location'])) {
            return;
        }
        
        // Update existing combination pages with new term data
        $this->update_combination_pages($term_id, $taxonomy);
    }
    
    public function handle_deleted_term($term_id, $tt_id, $taxonomy, $deleted_term) {
        if (!in_array($taxonomy, ['specialty', 'location'])) {
            return;
        }
        
        // Handle deletion of combination pages
        $this->handle_term_deletion($term_id, $taxonomy);
    }
    
    private function trigger_combination_generation($term_id, $taxonomy) {
        // Queue background task to generate combinations
        wp_schedule_single_event(time() + 60, 'generate_combinations_for_term', [$term_id, $taxonomy]);
    }
    
    private function update_combination_pages($term_id, $taxonomy) {
        global $wpdb;
        
        $column = $taxonomy === 'specialty' ? 'specialty_term_id' : 'location_term_id';
        
        // Get affected combination pages
        $combinations = $wpdb->get_results($wpdb->prepare("
            SELECT * FROM {$wpdb->prefix}taxonomy_combination_pages 
            WHERE $column = %d AND page_id IS NOT NULL
        ", $term_id));
        
        // Queue updates for each combination page
        foreach ($combinations as $combo) {
            wp_schedule_single_event(time() + 30, 'update_combination_page', [$combo->page_id]);
        }
    }
    
    private function handle_term_deletion($term_id, $taxonomy) {
        global $wpdb;
        
        $column = $taxonomy === 'specialty' ? 'specialty_term_id' : 'location_term_id';
        
        // Get affected combination pages
        $combinations = $wpdb->get_results($wpdb->prepare("
            SELECT page_id FROM {$wpdb->prefix}taxonomy_combination_pages 
            WHERE $column = %d AND page_id IS NOT NULL
        ", $term_id));
        
        // Move pages to trash or delete
        foreach ($combinations as $combo) {
            wp_trash_post($combo->page_id);
        }
        
        // Remove from tracking table
        $wpdb->delete(
            $wpdb->prefix . 'taxonomy_combination_pages',
            [$column => $term_id],
            ['%d']
        );
    }
}

// Register background tasks
add_action('generate_combinations_for_term', 'handle_generate_combinations_for_term', 10, 2);
add_action('update_combination_page', 'handle_update_combination_page', 10, 1);

function handle_generate_combinations_for_term($term_id, $taxonomy) {
    // Execute Python script to generate combinations
    $command = sprintf(
        'cd %s/../ && python3 combination_page_manager.py --generate-for-term %d %s 2>&1',
        ABSPATH,
        $term_id,
        $taxonomy
    );
    
    $output = shell_exec($command);
    
    // Log the result
    error_log("Generated combinations for term $term_id ($taxonomy): " . $output);
}

function handle_update_combination_page($page_id) {
    // Execute Python script to update combination page
    $command = sprintf(
        'cd %s/../ && python3 combination_page_manager.py --update-page %d 2>&1',
        ABSPATH,
        $page_id
    );
    
    $output = shell_exec($command);
    
    // Log the result
    error_log("Updated combination page $page_id: " . $output);
}
```

## Phase 7: Web Interface Integration

### 7.1 React Component for Combination Management
**File**: `web-interface/TaxonomyCombinations/CombinationManager.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { Button, Table, Card, Space, Tag, Modal, message, Spin, Progress } from 'antd';
import { PlusOutlined, SyncOutlined, EyeOutlined, EditOutlined } from '@ant-design/icons';
import { API_BASE_URL, API_ENDPOINTS } from '../../config/api';
import BatchCreationModal from './BatchCreationModal';
import GreenshiftPreview from './GreenshiftPreview';

interface CombinationPage {
  id: number;
  specialty_name: string;
  location_name: string;
  page_id?: number;
  status: 'pending' | 'created' | 'ai_generated' | 'published';
  provider_count?: number;
  created_at: string;
  post_title?: string;
  post_status?: string;
}

const CombinationManager: React.FC = () => {
  const [combinations, setCombinations] = useState<CombinationPage[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [batchModalVisible, setBatchModalVisible] = useState(false);
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [selectedCombination, setSelectedCombination] = useState<CombinationPage | null>(null);

  useEffect(() => {
    loadCombinations();
  }, []);

  const loadCombinations = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/healthcare/v1/combinations`);
      const data = await response.json();
      setCombinations(data);
    } catch (error) {
      message.error('Failed to load combination pages');
      console.error('Error loading combinations:', error);
    } finally {
      setLoading(false);
    }
  };

  const scanMissingCombinations = async () => {
    try {
      setScanning(true);
      const response = await fetch(`${API_BASE_URL}/healthcare/v1/combinations/scan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const result = await response.json();
      
      if (result.success) {
        message.success('Scan completed successfully');
        loadCombinations(); // Refresh the list
      } else {
        message.error('Scan failed');
      }
    } catch (error) {
      message.error('Failed to scan combinations');
      console.error('Error scanning:', error);
    } finally {
      setScanning(false);
    }
  };

  const handlePreview = (combination: CombinationPage) => {
    setSelectedCombination(combination);
    setPreviewModalVisible(true);
  };

  const getStatusColor = (status: string) => {
    const colors = {
      pending: 'orange',
      created: 'blue',
      ai_generated: 'green',
      published: 'success'
    };
    return colors[status as keyof typeof colors] || 'default';
  };

  const columns = [
    {
      title: 'Specialty',
      dataIndex: 'specialty_name',
      key: 'specialty_name',
      sorter: (a: CombinationPage, b: CombinationPage) => a.specialty_name.localeCompare(b.specialty_name),
    },
    {
      title: 'Location',
      dataIndex: 'location_name',
      key: 'location_name',
      sorter: (a: CombinationPage, b: CombinationPage) => a.location_name.localeCompare(b.location_name),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {status.replace('_', ' ').toUpperCase()}
        </Tag>
      ),
      filters: [
        { text: 'Pending', value: 'pending' },
        { text: 'Created', value: 'created' },
        { text: 'AI Generated', value: 'ai_generated' },
        { text: 'Published', value: 'published' },
      ],
      onFilter: (value: any, record: CombinationPage) => record.status === value,
    },
    {
      title: 'Providers',
      dataIndex: 'provider_count',
      key: 'provider_count',
      render: (count: number) => count || 0,
      sorter: (a: CombinationPage, b: CombinationPage) => (a.provider_count || 0) - (b.provider_count || 0),
    },
    {
      title: 'WordPress',
      key: 'wordpress_status',
      render: (_: any, record: CombinationPage) => {
        if (record.page_id) {
          return (
            <Tag color="green">
              {record.post_status?.toUpperCase() || 'CREATED'}
            </Tag>
          );
        }
        return <Tag color="red">NOT CREATED</Tag>;
      },
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString(),
      sorter: (a: CombinationPage, b: CombinationPage) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: CombinationPage) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handlePreview(record)}
            disabled={!record.page_id}
          >
            Preview
          </Button>
          {record.page_id && (
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => window.open(`/wp-admin/post.php?post=${record.page_id}&action=edit`, '_blank')}
            >
              Edit
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card title="Combination Pages Management">
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setBatchModalVisible(true)}
            >
              Batch Create Pages
            </Button>
            <Button
              icon={<SyncOutlined />}
              onClick={scanMissingCombinations}
              loading={scanning}
            >
              Scan Missing Combinations
            </Button>
            <Button onClick={loadCombinations} loading={loading}>
              Refresh
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={combinations}
          loading={loading}
          rowKey="id"
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} combinations`,
          }}
        />
      </Card>

      <BatchCreationModal
        visible={batchModalVisible}
        onClose={() => setBatchModalVisible(false)}
        onSuccess={() => {
          setBatchModalVisible(false);
          loadCombinations();
        }}
      />

      <Modal
        title="Combination Page Preview"
        open={previewModalVisible}
        onCancel={() => setPreviewModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedCombination && (
          <GreenshiftPreview combination={selectedCombination} />
        )}
      </Modal>
    </div>
  );
};

export default CombinationManager;
```

### 7.2 Batch Creation Modal
**File**: `web-interface/TaxonomyCombinations/BatchCreationModal.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { Modal, Table, Button, Space, Switch, message, Progress, Alert } from 'antd';
import { API_BASE_URL } from '../../config/api';

interface MissingCombination {
  specialty: {
    term_id: number;
    name: string;
    slug: string;
  };
  location: {
    term_id: number;
    name: string;
    slug: string;
  };
  provider_count: number;
}

interface BatchCreationModalProps {
  visible: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const BatchCreationModal: React.FC<BatchCreationModalProps> = ({
  visible,
  onClose,
  onSuccess,
}) => {
  const [missingCombinations, setMissingCombinations] = useState<MissingCombination[]>([]);
  const [selectedCombinations, setSelectedCombinations] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [autoAiContent, setAutoAiContent] = useState(true);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (visible) {
      loadMissingCombinations();
    }
  }, [visible]);

  const loadMissingCombinations = async () => {
    try {
      setLoading(true);
      // This would be implemented in your Python backend
      const response = await fetch(`${API_BASE_URL}/api/combinations/missing`);
      const data = await response.json();
      setMissingCombinations(data);
      setSelectedCombinations(data.map((_: any, index: number) => index));
    } catch (error) {
      message.error('Failed to load missing combinations');
      console.error('Error loading missing combinations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBatch = async () => {
    if (selectedCombinations.length === 0) {
      message.warning('Please select at least one combination to create');
      return;
    }

    try {
      setCreating(true);
      setProgress(0);

      const combinationsToCreate = selectedCombinations.map(index => missingCombinations[index]);

      const response = await fetch(`${API_BASE_URL}/healthcare/v1/combinations/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          combinations: combinationsToCreate,
          auto_ai_content: autoAiContent,
        }),
      });

      const result = await response.json();

      if (result.success) {
        message.success(`Successfully created ${selectedCombinations.length} combination pages`);
        onSuccess();
      } else {
        message.error('Failed to create combination pages');
      }
    } catch (error) {
      message.error('Failed to create combination pages');
      console.error('Error creating combinations:', error);
    } finally {
      setCreating(false);
      setProgress(0);
    }
  };

  const columns = [
    {
      title: 'Specialty',
      key: 'specialty',
      render: (_: any, record: MissingCombination) => record.specialty.name,
    },
    {
      title: 'Location',
      key: 'location',
      render: (_: any, record: MissingCombination) => record.location.name,
    },
    {
      title: 'Providers',
      dataIndex: 'provider_count',
      key: 'provider_count',
    },
    {
      title: 'URL Preview',
      key: 'url_preview',
      render: (_: any, record: MissingCombination) => (
        <code>
          /english-{record.specialty.slug}-{record.location.slug}/
        </code>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys: selectedCombinations,
    onChange: (selectedRowKeys: React.Key[]) => {
      setSelectedCombinations(selectedRowKeys as number[]);
    },
    onSelectAll: (selected: boolean, selectedRows: MissingCombination[], changeRows: MissingCombination[]) => {
      if (selected) {
        setSelectedCombinations(missingCombinations.map((_, index) => index));
      } else {
        setSelectedCombinations([]);
      }
    },
  };

  return (
    <Modal
      title="Batch Create Combination Pages"
      open={visible}
      onCancel={onClose}
      width={1000}
      footer={[
        <Button key="cancel" onClick={onClose} disabled={creating}>
          Cancel
        </Button>,
        <Button
          key="create"
          type="primary"
          onClick={handleCreateBatch}
          loading={creating}
          disabled={selectedCombinations.length === 0}
        >
          Create {selectedCombinations.length} Pages
        </Button>,
      ]}
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        <Alert
          message="Missing Combination Pages"
          description="These specialty/location combinations have providers but no dedicated pages yet."
          type="info"
          showIcon
        />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>
            Selected: {selectedCombinations.length} of {missingCombinations.length} combinations
          </span>
          <Space>
            <span>Generate AI Content:</span>
            <Switch
              checked={autoAiContent}
              onChange={setAutoAiContent}
              checkedChildren="Yes"
              unCheckedChildren="No"
            />
          </Space>
        </div>

        {creating && (
          <Progress
            percent={progress}
            status="active"
            strokeColor={{
              from: '#108ee9',
              to: '#87d068',
            }}
          />
        )}

        <Table
          columns={columns}
          dataSource={missingCombinations}
          loading={loading}
          rowKey={(record, index) => index!}
          rowSelection={rowSelection}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
          }}
          size="small"
        />
      </Space>
    </Modal>
  );
};

export default BatchCreationModal;
```

## Phase 8: Integration with Healthcare Directory Automation

### 8.1 Extended Automation Script
**File**: `run_combination_automation.py`

```python
#!/usr/bin/env python3
"""
Extended Healthcare Directory Automation with Combination Page Management
"""

import argparse
import logging
from datetime import datetime
from combination_page_manager import CombinationPageManager
from ai_combination_content import CombinationContentGenerator
from activity_logger import activity_logger

# Import existing automation modules
from run_automation import main as run_main_automation
from run_mega_batch_automation import main as run_mega_batch

def main():
    parser = argparse.ArgumentParser(description='Healthcare Directory + Combination Pages Automation')
    
    # Existing automation options
    parser.add_argument('--daily-limit', type=int, default=50, help='Daily processing limit')
    parser.add_argument('--all-providers', action='store_true', help='Process all providers')
    parser.add_argument('--stats-only', action='store_true', help='Show stats only')
    
    # New combination page options
    parser.add_argument('--scan-combinations', action='store_true', help='Scan for missing combinations')
    parser.add_argument('--create-combinations', action='store_true', help='Create missing combination pages')
    parser.add_argument('--update-provider-counts', action='store_true', help='Update provider counts')
    parser.add_argument('--generate-ai-combinations', action='store_true', help='Generate AI content for combinations')
    parser.add_argument('--combination-limit', type=int, default=10, help='Limit for combination processing')
    
    args = parser.parse_args()
    
    # Initialize managers
    combination_manager = CombinationPageManager()
    content_generator = CombinationContentGenerator()
    
    try:
        # Run existing healthcare directory automation first
        if not args.stats_only:
            print("=== Running Healthcare Directory Automation ===")
            if args.all_providers:
                run_mega_batch()
            else:
                run_main_automation()
        
        # Combination page automation
        if args.scan_combinations or args.create_combinations:
            print("\n=== Combination Pages Automation ===")
            
            # Scan for missing combinations
            missing_combinations = combination_manager.scan_missing_combinations()
            print(f"Found {len(missing_combinations)} missing combinations")
            
            activity_logger.log_activity(
                activity_type='scan_combinations',
                activity_category='taxonomy_combinations',
                description=f"Scanned combinations, found {len(missing_combinations)} missing",
                details={'missing_count': len(missing_combinations)},
                status='success'
            )
            
            if args.create_combinations and missing_combinations:
                # Limit processing
                to_process = missing_combinations[:args.combination_limit]
                print(f"Creating {len(to_process)} combination pages...")
                
                results = combination_manager.batch_create_combinations(
                    to_process, 
                    auto_ai_content=args.generate_ai_combinations
                )
                
                successful = sum(1 for r in results if r['success'])
                print(f"Successfully created {successful}/{len(to_process)} combination pages")
                
                activity_logger.log_activity(
                    activity_type='create_combinations_batch',
                    activity_category='taxonomy_combinations',
                    description=f"Created {successful} combination pages",
                    details={
                        'requested': len(to_process),
                        'successful': successful,
                        'auto_ai_content': args.generate_ai_combinations
                    },
                    status='success' if successful == len(to_process) else 'partial'
                )
        
        # Update provider counts for existing combinations
        if args.update_provider_counts:
            print("\n=== Updating Provider Counts ===")
            combination_manager.update_provider_counts()
            
            activity_logger.log_activity(
                activity_type='update_provider_counts',
                activity_category='taxonomy_combinations',
                description="Updated provider counts for all combination pages",
                status='success'
            )
        
        # Generate AI content for existing combinations without content
        if args.generate_ai_combinations:
            print("\n=== Generating AI Content for Combinations ===")
            
            # Get combinations needing AI content
            combinations_needing_content = combination_manager.get_combinations_needing_ai_content()
            
            if combinations_needing_content:
                to_process = combinations_needing_content[:args.combination_limit]
                content_generator.process_combination_batch(to_process)
                
                activity_logger.log_activity(
                    activity_type='generate_ai_content_combinations',
                    activity_category='taxonomy_combinations',
                    description=f"Generated AI content for {len(to_process)} combinations",
                    details={'processed_count': len(to_process)},
                    status='success'
                )
        
        # Display stats
        if args.stats_only or any([args.scan_combinations, args.create_combinations]):
            print("\n=== Combination Pages Statistics ===")
            stats = combination_manager.get_combination_stats()
            
            print(f"Total combinations: {stats['total']}")
            print(f"Published pages: {stats['published']}")
            print(f"With AI content: {stats['ai_generated']}")
            print(f"Pending creation: {stats['pending']}")
            print(f"Average providers per combination: {stats['avg_providers']:.1f}")
    
    except Exception as e:
        print(f"Error in combination automation: {str(e)}")
        activity_logger.log_activity(
            activity_type='combination_automation_error',
            activity_category='taxonomy_combinations',
            description=f"Automation failed: {str(e)}",
            status='error',
            error_message=str(e)
        )
        raise

if __name__ == "__main__":
    main()
```

### 8.2 API Endpoints Extension
**File**: `web-interface/api-extensions/combination-endpoints.py`

```python
from flask import Blueprint, request, jsonify
from combination_page_manager import CombinationPageManager
from ai_combination_content import CombinationContentGenerator
from activity_logger import activity_logger
import json

# Create blueprint for combination endpoints
combination_bp = Blueprint('combinations', __name__, url_prefix='/api/combinations')

# Initialize managers
combination_manager = CombinationPageManager()
content_generator = CombinationContentGenerator()

@combination_bp.route('/missing', methods=['GET'])
def get_missing_combinations():
    """Get combinations that need pages created"""
    try:
        missing = combination_manager.scan_missing_combinations()
        return jsonify(missing)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@combination_bp.route('/stats', methods=['GET'])
def get_combination_stats():
    """Get combination pages statistics"""
    try:
        stats = combination_manager.get_combination_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@combination_bp.route('/batch-create', methods=['POST'])
def batch_create_combinations():
    """Create multiple combination pages"""
    try:
        data = request.get_json()
        combinations = data.get('combinations', [])
        auto_ai_content = data.get('auto_ai_content', True)
        
        if not combinations:
            return jsonify({'error': 'No combinations provided'}), 400
        
        # Process batch creation
        results = combination_manager.batch_create_combinations(
            combinations, 
            auto_ai_content
        )
        
        successful = sum(1 for r in results if r['success'])
        
        # Log activity
        activity_logger.log_activity(
            activity_type='batch_create_combinations_api',
            activity_category='taxonomy_combinations',
            description=f"API batch created {successful}/{len(combinations)} combinations",
            details={
                'requested': len(combinations),
                'successful': successful,
                'auto_ai_content': auto_ai_content,
                'results': results
            },
            status='success' if successful == len(combinations) else 'partial'
        )
        
        return jsonify({
            'success': True,
            'created': successful,
            'total': len(combinations),
            'results': results
        })
        
    except Exception as e:
        activity_logger.log_activity(
            activity_type='batch_create_combinations_api',
            activity_category='taxonomy_combinations',
            description=f"API batch creation failed: {str(e)}",
            status='error',
            error_message=str(e)
        )
        return jsonify({'error': str(e)}), 500

@combination_bp.route('/generate-ai-content', methods=['POST'])
def generate_ai_content():
    """Generate AI content for combinations"""
    try:
        data = request.get_json()
        combination_ids = data.get('combination_ids', [])
        
        if not combination_ids:
            return jsonify({'error': 'No combination IDs provided'}), 400
        
        # Get combination data
        combinations = []
        for combo_id in combination_ids:
            combo_data = combination_manager.get_combination_by_id(combo_id)
            if combo_data:
                combinations.append(combo_data)
        
        # Process AI content generation
        content_generator.process_combination_batch(combinations)
        
        activity_logger.log_activity(
            activity_type='generate_ai_content_api',
            activity_category='taxonomy_combinations',
            description=f"Generated AI content for {len(combinations)} combinations via API",
            details={'combination_ids': combination_ids},
            status='success'
        )
        
        return jsonify({
            'success': True,
            'processed': len(combinations)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@combination_bp.route('/update-provider-counts', methods=['POST'])
def update_provider_counts():
    """Update provider counts for all combinations"""
    try:
        combination_manager.update_provider_counts()
        
        activity_logger.log_activity(
            activity_type='update_provider_counts_api',
            activity_category='taxonomy_combinations',
            description="Updated provider counts via API",
            status='success'
        )
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@combination_bp.route('/<int:combination_id>/preview', methods=['GET'])
def preview_combination(combination_id):
    """Get preview data for a combination page"""
    try:
        combination = combination_manager.get_combination_by_id(combination_id)
        
        if not combination:
            return jsonify({'error': 'Combination not found'}), 404
        
        # Get preview data including providers
        preview_data = {
            'combination': combination,
            'providers': combination_manager.get_providers_for_combination(combination_id),
            'content_preview': combination_manager.get_content_preview(combination_id)
        }
        
        return jsonify(preview_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Register blueprint in main Flask app
def register_combination_endpoints(app):
    app.register_blueprint(combination_bp)
```

## Implementation Summary

This comprehensive implementation plan provides:

### 🎯 **Core Features**
- **Automatic Page Creation**: WordPress hooks detect new specialties/locations and trigger page generation
- **Blocksy Pro Integration**: Native theme templates and responsive design
- **Greenshift Dynamic Content**: Visual page building with dynamic provider queries  
- **ACF Pro Field Management**: Structured custom fields for all page data
- **AI Content Generation**: Claude-powered descriptions integrated with existing mega-batch system
- **Yoast SEO Automation**: Pre-populated SEO fields and schema markup

### 🔧 **Technical Integration**
- **Healthcare Directory Sync**: Full integration with existing provider automation
- **Web Interface**: React components for management and monitoring
- **Activity Logging**: Comprehensive tracking of all operations
- **Database Extensions**: Proper tracking and relationship management
- **API Endpoints**: RESTful interfaces for all operations

### 🚀 **Automation Workflow**
1. **Detection**: New taxonomy terms trigger combination scan
2. **Creation**: Missing combinations automatically generate pages
3. **Template Application**: Blocksy templates and Greenshift patterns applied
4. **Content Generation**: AI descriptions created via existing Claude integration
5. **SEO Optimization**: Yoast fields populated with smart defaults
6. **Monitoring**: Activity logging and web interface tracking

### 📊 **Management Features**
- **Batch Operations**: Create multiple pages simultaneously
- **Provider Count Updates**: Automatic synchronization with directory data
- **Content Previews**: Greenshift-powered page previews
- **Status Tracking**: Complete lifecycle monitoring
- **Manual Override**: Easy editing of titles, descriptions, and SEO data

This plan leverages your existing plugin ecosystem while providing the automation and AI integration you need for scalable specialty/location combination pages.