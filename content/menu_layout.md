# Menu Layout Guide - Care Compass Japan

**Reference for building mega-menu navigation using Blocksy theme**

## Overview

This guide adapts proven Japanese travel site navigation patterns for Care Compass Japan's healthcare directory. Based on SEO analysis showing users search "[specialty] in [location]" (e.g., "dentist in tokyo"), the layout prioritizes specialty-first navigation with location filtering.

---

## SEO-Informed Navigation Strategy

### User Search Behavior Analysis
**Primary Search Pattern:** "[Specialty] in [Location]"
- dentist in tokyo
- cardiologist in osaka  
- ENT doctor in yokohama
- english speaking doctor in shibuya

**Key Insight:** Users think **SPECIALTY-FIRST**, then location. Navigation should match this mental model.

### Final Recommended Navigation Structure
```
[Care Compass Logo] | Medical Specialties | Cities | Find Doctors | Emergency | [🔍 Search] | [Account]
```

**Navigation Priority:**
1. **Medical Specialties** = Primary user intent (specialty-first)
2. **Cities** = Secondary user intent (location-first)  
3. **Find Doctors** = General search (covers all cases)
4. **Emergency** = Specialized need

---

## Tab 1: Medical Specialties (Primary)

### Layout: Featured Specialties + Specialty-Location Matrix

#### Featured Medical Specialties (3 large cards with medical icons)
```
[Dentistry Icon]            [Cardiology Icon]           [ENT Icon]
Dentistry                   Cardiology                  ENT (Ear, Nose, Throat)
300+ English-speaking       120+ Heart specialists      85+ ENT specialists
dentists nationwide         across Japan                nationwide
[Find Dentists >]          [Find Cardiologists >]      [Find ENT Doctors >]
```

#### Complete Specialty-Location Matrix (4 columns)
```
Primary Care                Specialist Care             Emergency & Urgent         Dental & Oral
------------                ---------------             ------------------         -------------
General Medicine            Cardiology                  Emergency Medicine         General Dentistry
• Tokyo (200+)              • Tokyo (45+)               • Tokyo (15+ centers)      • Tokyo (150+)
• Osaka (100+)              • Osaka (20+)               • Osaka (8+ centers)       • Osaka (75+)
• Yokohama (80+)            • Yokohama (15+)            • Yokohama (6+ centers)    • Yokohama (50+)

Internal Medicine           Dermatology                 Urgent Care Clinics        Oral Surgery
• Tokyo (150+)              • Tokyo (60+)               • Tokyo (25+ clinics)      • Tokyo (40+)
• Osaka (80+)               • Osaka (35+)               • Osaka (15+ clinics)      • Osaka (20+)
• Yokohama (60+)            • Yokohama (25+)            • Yokohama (12+ clinics)   • Yokohama (15+)

Family Medicine             ENT (Ear, Nose, Throat)    Walk-in Clinics           Cosmetic Dentistry
• Tokyo (120+)              • Tokyo (35+)               • Tokyo (30+ clinics)      • Tokyo (60+)
• Osaka (65+)               • Osaka (15+)               • Osaka (18+ clinics)      • Osaka (25+)
• Yokohama (45+)            • Yokohama (12+)            • Yokohama (15+ clinics)   • Yokohama (20+)

Gynecology                  Orthopedics                 Mental Health              Pediatric Dentistry
• Tokyo (80+)               • Tokyo (50+)               • Tokyo (40+)              • Tokyo (35+)
• Osaka (40+)               • Osaka (25+)               • Osaka (20+)              • Osaka (18+)
• Yokohama (35+)            • Yokohama (20+)            • Yokohama (15+)           • Yokohama (12+)
```

**Each specialty-location link goes to:** `/[specialty]-[city]/` (e.g., `/dentist-tokyo/`)
**Hover behavior:** Show provider count and average rating
**Visual treatment:** Most popular combinations highlighted

---

## Tab 2: Cities (Secondary)

### Layout: Location-First with Specialty Breakdown

#### Featured Healthcare Cities (3 large cards with city skylines)
```
[Tokyo Skyline]             [Osaka Skyline]            [Yokohama Skyline]
Tokyo                       Osaka                      Yokohama
500+ English-speaking       200+ Verified              150+ International
providers                   providers                  providers
[Browse Tokyo Healthcare >] [Browse Osaka Healthcare >] [Browse Yokohama Healthcare >]
```

#### Complete City-Specialty Matrix (3 columns)
```
Major Cities                Regional Cities             Specialized Areas
------------                ---------------             -----------------
Tokyo                       Fukuoka                     Okinawa
• Dentistry (150+)          • Dentistry (35+)           • Dentistry (15+)
• Cardiology (45+)          • Cardiology (15+)          • General Medicine (25+)
• ENT (35+)                 • ENT (12+)                 • Emergency Care (3+)
• General Medicine (200+)   • General Medicine (50+)    
• Emergency Care (15+)      • Emergency Care (5+)       Hot Springs Medical
                                                        • Rehabilitation (10+)
Osaka                       Kyoto                       • Wellness Centers (8+)
• Dentistry (75+)           • Dentistry (25+)           • Medical Tourism (5+)
• Cardiology (20+)          • Cardiology (8+)           
• ENT (15+)                 • ENT (6+)                  Tokyo Districts
• General Medicine (100+)   • General Medicine (40+)    • Shibuya (80+ providers)
• Emergency Care (8+)       • Emergency Care (3+)       • Minato (70+ providers)
                                                        • Shinjuku (65+ providers)
Yokohama                    Sapporo                     • Chiyoda (45+ providers)
• Dentistry (50+)           • Dentistry (30+)           • Setagaya (40+ providers)
• Cardiology (15+)          • Cardiology (10+)          
• ENT (12+)                 • ENT (8+)                  Osaka Districts
• General Medicine (80+)    • General Medicine (35+)    • Kita Ward (60+ providers)
• Emergency Care (6+)       • Emergency Care (4+)       • Chuo Ward (45+ providers)
                                                        • Namba Area (35+ providers)
```

**Each city-specialty link goes to:** `/[specialty]-[city]/` (same URLs as Tab 1)
**Hover behavior:** Show top 3 specialties for each city
**Visual treatment:** Major cities prominently featured, districts as sub-items

---

## Tab 3: Find Doctors (General Search)

### Layout: Search Interface + Quick Access

#### Unified Search Interface
```
[Search Bar: "Find English-speaking doctors in Japan"]
[Specialty Dropdown ▼] [in] [City Dropdown ▼] [English Level ▼] [Search Button]

Popular Searches:
• dentist in tokyo          • cardiologist in osaka         • ENT doctor in yokohama
• emergency care tokyo      • english doctor shibuya        • gynecologist osaka
```

#### Quick Access Categories (4 columns)
```
By Urgency                 By Patient Type            By Language Support        By Insurance
----------                 ---------------            -------------------        ------------
Emergency Care             Women's Health             Fluent English (200+)      Japanese National
• Tokyo (15+ centers)      • Gynecology (60+)         • Tokyo (150+)             Health Insurance
• Osaka (8+ centers)       • Pregnancy Care (25+)     • Osaka (75+)              
• Available 24/7           • Fertility (15+)          • Yokohama (50+)           International
                                                                                  Insurance
Same-Day Care              Men's Health               Conversational English     • Accepted (300+)
• Walk-in Clinics (70+)    • Urology (15+)           (350+)                     • Direct Payment
• Urgent Care (40+)        • Cardiology (45+)         • Tokyo (200+)             • Travel Insurance
• Evening Hours            • Sports Medicine (20+)     • Osaka (100+)             

Routine Care               Children's Health          Basic English (150+)       Medical Tourism
• General Medicine (400+)  • Pediatrics (30+)         • All cities               • Packages Available
• Preventive Care (200+)   • Pediatric Dentistry      • Translation Support      • Hotel Partnerships
• Health Screenings        (35+)                      Available                   • Airport Pickup
```

#### Advanced Search Options (Expandable)
```
[+ Advanced Filters]
• Accessibility: Wheelchair accessible, Parking available
• Appointment: Same-day, Online booking, Evening hours
• Services: Telemedicine, Home visits, Medical tourism
• Certifications: Board certified, International training
```

**Search functionality:**
- Auto-complete with popular searches
- Filter combinations (specialty + location + language + urgency)
- Results show provider cards with ratings, photos, availability
- Direct links to `/[specialty]-[city]/` landing pages

---

## Tab 4: Emergency (Specialized)

### Layout: Immediate Access + Emergency Resources

#### Emergency Contact Banner
```
🚨 EMERGENCY: Call 119 (Ambulance) | 110 (Police) | #7119 (Medical Advice)
```

#### Emergency Healthcare Access (3 columns)
```
24/7 Emergency Centers      English-Speaking Emergency  Emergency Phrases
-----------------------     -------------------------   -----------------
Tokyo                       St. Luke's International    "Kyukyu desu" (Emergency)
• St. Luke's International  • 24/7 English Support      "Itai desu" (It hurts)
• Tokyo Medical Center      • International Insurance   "Byoin e" (To hospital)
• Jikei University          • Direct Admission          "Denwa shite" (Call)
                                                        "Tasukete" (Help)
Osaka                       Osaka Red Cross             
• Osaka Red Cross          • 24/7 English Support      Emergency Numbers
• Osaka General Hospital   • International Patients    • Ambulance: 119
• Sumitomo Hospital        • Emergency Translation      • Police: 110
                                                        • Medical Advice: #7119
Yokohama                   Yokohama City Hospital      • Tokyo Fire: 03-3212-2111
• Yokohama City Hospital   • Emergency English Staff   • Osaka Fire: 06-6582-5253
• Kanagawa Children's      • 24/7 Access              
• Saiseikai Yokohama       • Insurance Accepted        
```

#### Emergency Preparation (2 columns)
```
Before Emergency                    What to Bring
----------------                    -------------
• Save emergency numbers in phone  • Health Insurance Card
• Know nearest hospital address     • Passport/ID
• Learn basic Japanese phrases      • Medication List
• Register with embassy             • Emergency Contact Info
• Keep insurance cards handy        • Cash for payment
```

**Emergency features:**
- Large, prominent emergency numbers
- Direct links to hospital emergency departments
- Downloadable emergency phrase cards
- GPS directions to nearest emergency care

## SEO Landing Page Strategy

### URL Structure Based on User Search Intent
```
Primary Landing Pages (match "[specialty] in [location]" searches):
/dentist-tokyo/
/cardiologist-osaka/
/ent-doctor-yokohama/
/english-doctor-shibuya/
/emergency-care-tokyo/

Secondary Pages (alternative search patterns):
/tokyo-dentist/ → 301 redirect to /dentist-tokyo/
/osaka-cardiology/ → 301 redirect to /cardiologist-osaka/
/yokohama-ent/ → 301 redirect to /ent-doctor-yokohama/
```

### Navigation-to-Landing Page Mapping
```
Medical Specialties Tab → Dentistry → Tokyo → /dentist-tokyo/
Cities Tab → Tokyo → Dentistry → /dentist-tokyo/
Find Doctors Tab → Search Results → /dentist-tokyo/
Emergency Tab → Emergency Care → Tokyo → /emergency-care-tokyo/
```

### Content Strategy for Landing Pages
```
Each /[specialty]-[city]/ page includes:
• SEO-optimized title: "English-Speaking Dentists in Tokyo | Care Compass"
• Meta description: "Find verified English-speaking dentists in Tokyo..."
• Provider listings with ratings, photos, availability
• Local area information (districts, stations, accessibility)
• Emergency contact information specific to city
• Related specialties and nearby cities
```

---

## Design Specifications for Blocksy

### Visual Design Elements

#### Typography
```
Tab Labels: 16px, medium weight, primary color
Section Headers: 14px, bold, dark gray
Provider Counts: 12px, normal, accent color (green)
Location Names: 14px, normal, link color
Specialty Names: 14px, medium weight, primary color
```

#### Colors (Healthcare-Optimized)
```
Primary: Care Compass brand color (trustworthy blue)
Secondary: Light blue/teal for healthcare associations
Accent: Green for provider counts and success states
Emergency: Red for emergency sections (#dc3545)
Background: White with subtle gray borders (#f8f9fa)
Hover: Light blue background (#e3f2fd)
```

#### Spacing
```
Tab spacing: 40px between tabs
Column gaps: 30px between columns
Row spacing: 15px between rows
Card padding: 20px internal padding
Emergency banner: 10px padding, bold red background
```

### Blocksy Mega-Menu Configuration

#### Container Settings
```
Max Width: 1200px
Background: White (#ffffff)
Border: 1px solid #e5e5e5
Shadow: 0 4px 12px rgba(0,0,0,0.1)
Animation: Fade in (300ms)
Mobile breakpoint: 768px
```

#### Column Structure

**Medical Specialties Tab (Primary):**
```
Row 1: 3 columns (featured specialties) - 33% each
Row 2: 4 columns (specialty-location matrix) - 25% each
```

**Cities Tab (Secondary):**
```
Row 1: 3 columns (featured cities) - 33% each
Row 2: 3 columns (city-specialty matrix) - 33% each
```

**Find Doctors Tab (General Search):**
```
Row 1: 1 column (search interface) - 100% width
Row 2: 4 columns (quick access categories) - 25% each
Row 3: 1 column (advanced filters) - 100% width
```

**Emergency Tab (Specialized):**
```
Row 1: 1 column (emergency banner) - 100% width, red background
Row 2: 3 columns (emergency access) - 33% each
Row 3: 2 columns (emergency preparation) - 50% each
```

### Content Management

#### Dynamic Content Elements
```
Provider Counts: Pull from database, update weekly
Featured Specialties: Based on search volume + provider density
Popular Searches: Based on actual user search queries
Emergency Contacts: Verified quarterly for accuracy
Language Support Levels: Updated with provider verification
```

#### Static Content Elements
```
City Names: Fixed geographic structure
Specialty Categories: Standard medical classifications
Emergency Numbers: Japan national emergency system
Navigation Labels: Consistent UI terminology
Call-to-Action Text: Optimized for healthcare conversions
```

---

## Implementation Checklist

### Phase 1: Basic Structure
- [ ] Set up 3-tab mega-menu in Blocksy
- [ ] Configure column layouts for each tab
- [ ] Add basic geographic and specialty content
- [ ] Implement hover states and animations

### Phase 2: Content Integration
- [ ] Connect to provider database for counts
- [ ] Add featured area images and descriptions
- [ ] Implement specialty icons and descriptions
- [ ] Set up dynamic provider count updates

### Phase 3: Enhancement Features
- [ ] Add search functionality within mega-menu
- [ ] Implement provider density color coding
- [ ] Add "English support level" indicators
- [ ] Include accessibility information

### Phase 4: Mobile Optimization
- [ ] Design collapsed mobile menu version
- [ ] Implement touch-friendly interactions
- [ ] Optimize for mobile performance
- [ ] Test across different screen sizes

---

## Content Templates

### City/Region Link Format
```
<a href="/providers/[city-slug]">
  [City Name] 
  <span class="provider-count">([count]+ providers)</span>
</a>
```

### Featured Card Template
```
<div class="featured-healthcare-card">
  <img src="[city-image]" alt="[City] healthcare">
  <h3>[City Name]</h3>
  <p>[count]+ [description]</p>
  <a href="/providers/[city-slug]" class="cta-button">Find Providers ></a>
</div>
```

### Specialty Link Format
```
<a href="/providers/specialty/[specialty-slug]">
  [Specialty Name]
  <span class="provider-count">([count]+)</span>
</a>
```

---

## SEO Considerations

### URL Structure
```
Geographic Pages: /providers/[region]/[city]
Specialty Pages: /providers/specialty/[specialty-name]
Combined Pages: /providers/[city]/[specialty]
```

### Internal Linking Strategy
```
Each menu item links to optimized landing page
Landing pages include provider listings + local SEO content
Cross-link between geographic and specialty pages
Implement breadcrumb navigation
```

### Schema Markup
```
Use BreadcrumbList schema for navigation
Implement LocalBusiness schema on city pages
Add MedicalOrganization schema for specialty pages
Include aggregateRating data where available
```

---

## Performance Optimization

### Loading Strategy
```
Preload critical menu content
Lazy load provider counts via AJAX
Cache geographic data (rarely changes)
Optimize images for featured cards
```

### User Experience
```
Hover intent detection (300ms delay)
Keyboard navigation support
Mobile-first responsive design
Fast menu close on outside click
```

---

## Analytics Tracking

### Menu Interaction Events
```
Tab clicks: Track which sections are most popular
Link clicks: Monitor geographic vs. specialty preferences
Hover behavior: Understand user exploration patterns
Mobile usage: Track mobile menu performance
```

### Conversion Optimization
```
A/B test featured area selection
Monitor click-through rates by section
Track search behavior within mega-menu
Optimize based on user flow data
```

---

## Future Enhancements

### Advanced Features
```
Real-time provider availability
"Near me" location detection
Integrated appointment booking
Multi-language support (Japanese toggle)
Provider favoriting/comparison
```

### Content Expansions
```
Subspecialty breakdowns
Hospital vs. clinic filtering
Insurance acceptance indicators
Transportation accessibility
Telehealth availability
```

---

---

## Key Implementation Insights

### SEO-Driven Navigation Success Factors

**1. Match User Search Intent**
- Primary navigation = "Medical Specialties" (matches "[specialty] in [location]" searches)
- Secondary navigation = "Cities" (alternative search pattern)
- All paths lead to same URL structure: `/[specialty]-[city]/`

**2. Reduce Decision Fatigue**
- Eliminated redundant "Find Providers" vs "Specialties" vs "Locations" confusion
- Clear hierarchy: Specialty-first → Location-second → General search → Emergency

**3. Optimize for Mobile**
- Emergency access always visible
- Search functionality prominent
- Mega-menu collapses logically on mobile

**4. Provide Multiple Discovery Paths**
- Browse by specialty (primary user behavior)
- Browse by location (secondary user behavior)
- Search with filters (power users)
- Emergency access (urgent needs)

---

**Last Updated:** July 16, 2025
**Status:** SEO-optimized, ready for Blocksy implementation
**Next Steps:** Begin Phase 1 with Medical Specialties tab (primary user intent)
**Key Insight:** Navigation structure now matches "[specialty] in [location]" search behavior