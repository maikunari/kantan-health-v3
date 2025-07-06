#!/usr/bin/env python3
"""
Review Keyword Analyzer for Healthcare Directory

This script analyzes patient reviews to extract the most frequently mentioned
keywords and topics, providing valuable SEO and content insights.
"""

import re
import json
from collections import Counter
from textblob import TextBlob
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('punkt_tab')
    nltk.download('stopwords')
    nltk.download('wordnet')

class ReviewKeywordAnalyzer:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
        # Healthcare-specific stop words to exclude
        self.healthcare_stopwords = {
            'doctor', 'dr', 'clinic', 'hospital', 'medical', 'health',
            'patient', 'visit', 'time', 'place', 'staff',
            'go', 'went', 'get', 'got', 'come', 'came', 'see', 'saw',
            'good', 'great', 'nice', 'excellent', 'amazing', 'wonderful',
            'bad', 'terrible', 'awful', 'horrible', 'worst',
            'would', 'could', 'should', 'will', 'can', 'may', 'might',
            # Language-specific terms (we track English proficiency separately)
            'japanese', 'english', 'language', 'speak', 'speaking',
            # Generic location terms
            'japan', 'tokyo', 'osaka', 'location'
        }
        
        # Healthcare-specific valuable keywords to prioritize
        self.healthcare_priority_keywords = {
            # Services & Treatments
            'cleaning', 'checkup', 'examination', 'surgery', 'treatment',
            'consultation', 'screening', 'vaccination', 'therapy',
            
            # Specialties
            'pediatric', 'kids', 'children', 'family', 'emergency',
            'cosmetic', 'orthodontic', 'oral', 'dental', 'implant',
            
            # Insurance & Payment
            'insurance', 'payment', 'cost', 'price', 'expensive', 'affordable',
            'cash', 'credit', 'billing', 'coverage',
            
            # Service Quality & Experience (HIGH VALUE)
            'friendly', 'professional', 'experienced', 'skilled', 'gentle',
            'helpful', 'unhelpful', 'kind', 'patient', 'rude', 'pleasant',
            'unpleasant', 'caring', 'thorough', 'rushed', 'attentive',
            'dismissive', 'courteous', 'respectful', 'understanding',
            
            # Facility Quality (HIGH VALUE)
            'clean', 'dirty', 'modern', 'outdated', 'comfortable', 'cramped',
            'spacious', 'crowded', 'quiet', 'noisy', 'organized', 'chaotic',
            'equipment', 'facilities', 'technology', 'renovated',
            
            # Practical Information (HIGH VALUE)
            'parking', 'convenient', 'inconvenient', 'accessible', 'nearby',
            'station', 'walking', 'distance', 'elevator', 'stairs',
            'wheelchair', 'disabled', 'transportation',
            
            # Timing & Efficiency (HIGH VALUE)
            'waiting', 'quick', 'fast', 'slow', 'delayed', 'punctual',
            'efficient', 'appointment', 'schedule', 'hours', 'weekend',
            'evening', 'urgent', 'emergency',
            
            # Communication (SELECTIVE - no language names)
            'communication', 'explain', 'explanation', 'understanding',
            'translator', 'interpreter', 'bilingual',
            
            # Pain & Comfort (HIGH VALUE)
            'painful', 'painless', 'comfortable', 'uncomfortable', 'gentle',
            'rough', 'careful', 'soothing', 'relaxing', 'stressful'
        }
    
    def clean_and_tokenize(self, text):
        """Clean and tokenize review text"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stop words and lemmatize
        cleaned_tokens = []
        for token in tokens:
            if (len(token) > 2 and 
                token not in self.stop_words and 
                token not in self.healthcare_stopwords and
                token.isalpha()):
                
                lemmatized = self.lemmatizer.lemmatize(token)
                cleaned_tokens.append(lemmatized)
        
        return cleaned_tokens
    
    def extract_phrases(self, text, max_phrase_length=3):
        """Extract meaningful phrases from text"""
        # Clean text
        text = re.sub(r'[^a-zA-Z\s]', ' ', text.lower())
        tokens = text.split()
        
        phrases = []
        
        # Extract 2-word and 3-word phrases
        for i in range(len(tokens)):
            for phrase_len in range(2, max_phrase_length + 1):
                if i + phrase_len <= len(tokens):
                    phrase = ' '.join(tokens[i:i + phrase_len])
                    
                    # Filter out phrases with stop words
                    if not any(word in self.stop_words for word in phrase.split()):
                        phrases.append(phrase)
        
        return phrases
    
    def analyze_sentiment_by_keyword(self, reviews):
        """Analyze sentiment for each keyword"""
        keyword_sentiments = {}
        
        for review in reviews:
            text = review.get('text', '')
            rating = review.get('rating', 3)
            
            # Convert rating to sentiment score (-1 to 1)
            sentiment_score = (rating - 3) / 2  # 5 stars = 1, 1 star = -1
            
            tokens = self.clean_and_tokenize(text)
            
            for token in tokens:
                if token in self.healthcare_priority_keywords:
                    if token not in keyword_sentiments:
                        keyword_sentiments[token] = []
                    keyword_sentiments[token].append(sentiment_score)
        
        # Calculate average sentiment for each keyword
        keyword_sentiment_avg = {}
        for keyword, sentiments in keyword_sentiments.items():
            keyword_sentiment_avg[keyword] = {
                'avg_sentiment': sum(sentiments) / len(sentiments),
                'mention_count': len(sentiments),
                'sentiment_label': self.get_sentiment_label(sum(sentiments) / len(sentiments))
            }
        
        return keyword_sentiment_avg
    
    def get_sentiment_label(self, score):
        """Convert sentiment score to label"""
        if score >= 0.3:
            return 'Positive'
        elif score <= -0.3:
            return 'Negative'
        else:
            return 'Neutral'
    
    def extract_service_keywords(self, reviews):
        """Extract service-specific keywords"""
        service_patterns = {
            'dental_services': [
                'cleaning', 'whitening', 'filling', 'crown', 'bridge',
                'implant', 'extraction', 'root canal', 'orthodontic',
                'braces', 'retainer', 'checkup', 'xray', 'examination'
            ],
            'medical_services': [
                'consultation', 'examination', 'surgery', 'treatment',
                'therapy', 'vaccination', 'screening', 'diagnosis',
                'prescription', 'medication', 'injection', 'test'
            ],
            'patient_experience': [
                'friendly', 'professional', 'gentle', 'painful', 'comfortable',
                'clean', 'modern', 'equipment', 'waiting', 'appointment'
            ],
            'language_support': [
                'english', 'japanese', 'translator', 'interpreter', 'language',
                'communication', 'explain', 'understanding', 'bilingual'
            ]
        }
        
        service_keywords = {category: Counter() for category in service_patterns}
        
        for review in reviews:
            text = review.get('text', '').lower()
            tokens = self.clean_and_tokenize(text)
            
            for category, keywords in service_patterns.items():
                for keyword in keywords:
                    if keyword in tokens:
                        service_keywords[category][keyword] += 1
        
        return service_keywords
    
    def analyze_provider_reviews(self, reviews):
        """Comprehensive analysis of provider reviews"""
        if not reviews:
            return {}
        
        all_text = ' '.join([review.get('text', '') for review in reviews])
        all_tokens = self.clean_and_tokenize(all_text)
        all_phrases = self.extract_phrases(all_text)
        
        # Get keyword frequencies
        keyword_freq = Counter(all_tokens)
        phrase_freq = Counter(all_phrases)
        
        # Filter to relevant healthcare keywords
        relevant_keywords = {
            k: v for k, v in keyword_freq.items() 
            if k in self.healthcare_priority_keywords and v >= 2
        }
        
        # Get sentiment analysis
        keyword_sentiments = self.analyze_sentiment_by_keyword(reviews)
        
        # Get service-specific keywords
        service_keywords = self.extract_service_keywords(reviews)
        
        # Combine everything
        analysis = {
            'top_keywords': dict(Counter(relevant_keywords).most_common(10)),
            'top_phrases': dict(Counter(phrase_freq).most_common(10)),
            'keyword_sentiments': keyword_sentiments,
            'service_categories': {
                category: dict(counter.most_common(5)) 
                for category, counter in service_keywords.items()
                if counter
            },
            'total_reviews': len(reviews),
            'avg_rating': sum(r.get('rating', 0) for r in reviews) / len(reviews) if reviews else 0
        }
        
        return analysis
    
    def generate_seo_insights(self, keyword_analysis):
        """Generate SEO insights from keyword analysis"""
        insights = {
            'primary_services': [],
            'content_opportunities': [],
            'faq_suggestions': [],
            'page_title_keywords': [],
            'meta_description_keywords': []
        }
        
        # Primary services from top keywords
        top_keywords = keyword_analysis.get('top_keywords', {})
        for keyword, count in top_keywords.items():
            if keyword in ['cleaning', 'checkup', 'treatment', 'consultation']:
                insights['primary_services'].append(f"{keyword.title()} ({count} mentions)")
        
        # Content opportunities
        service_categories = keyword_analysis.get('service_categories', {})
        for category, keywords in service_categories.items():
            if keywords:
                top_service = list(keywords.keys())[0]
                insights['content_opportunities'].append(
                    f"Create content about {top_service} (mentioned {keywords[top_service]} times)"
                )
        
        # FAQ suggestions based on keywords
        keyword_sentiments = keyword_analysis.get('keyword_sentiments', {})
        for keyword, data in keyword_sentiments.items():
            if data['mention_count'] >= 3:
                if keyword in ['insurance', 'cost', 'price']:
                    insights['faq_suggestions'].append(f"Do you accept insurance? (mentioned {data['mention_count']} times)")
                elif keyword in ['kids', 'children', 'pediatric']:
                    insights['faq_suggestions'].append(f"Do you treat children? (mentioned {data['mention_count']} times)")
                elif keyword in ['english', 'translator']:
                    insights['faq_suggestions'].append(f"Do you have English-speaking staff? (mentioned {data['mention_count']} times)")
        
        # SEO keywords for titles and meta descriptions
        insights['page_title_keywords'] = list(top_keywords.keys())[:5]
        insights['meta_description_keywords'] = list(top_keywords.keys())[:8]
        
        return insights

def analyze_provider_keywords(provider_name, reviews_data):
    """Analyze keywords for a specific provider"""
    analyzer = ReviewKeywordAnalyzer()
    
    print(f"🔍 Analyzing keywords for: {provider_name}")
    print("=" * 50)
    
    # Parse reviews if they're JSON string
    if isinstance(reviews_data, str):
        try:
            reviews = json.loads(reviews_data)
        except:
            reviews = []
    else:
        reviews = reviews_data or []
    
    if not reviews:
        print("❌ No reviews found for analysis")
        return {}
    
    # Perform analysis
    analysis = analyzer.analyze_provider_reviews(reviews)
    
    # Display results
    print(f"📊 Analysis Results ({analysis['total_reviews']} reviews, avg rating: {analysis['avg_rating']:.1f})")
    print()
    
    print("🏷️  TOP KEYWORDS:")
    for keyword, count in analysis['top_keywords'].items():
        sentiment_data = analysis['keyword_sentiments'].get(keyword, {})
        sentiment = sentiment_data.get('sentiment_label', 'Unknown')
        print(f"   • {keyword}: {count} mentions ({sentiment})")
    print()
    
    print("📝 TOP PHRASES:")
    for phrase, count in list(analysis['top_phrases'].items())[:5]:
        print(f"   • \"{phrase}\": {count} mentions")
    print()
    
    print("🏥 SERVICE CATEGORIES:")
    for category, keywords in analysis['service_categories'].items():
        if keywords:
            print(f"   {category.replace('_', ' ').title()}:")
            for keyword, count in list(keywords.items())[:3]:
                print(f"     - {keyword}: {count} mentions")
    print()
    
    # Generate SEO insights
    seo_insights = analyzer.generate_seo_insights(analysis)
    
    print("🎯 SEO INSIGHTS:")
    print("   Primary Services:")
    for service in seo_insights['primary_services'][:3]:
        print(f"     - {service}")
    print()
    print("   Content Opportunities:")
    for opportunity in seo_insights['content_opportunities'][:3]:
        print(f"     - {opportunity}")
    print()
    print("   FAQ Suggestions:")
    for faq in seo_insights['faq_suggestions'][:3]:
        print(f"     - {faq}")
    
    return analysis

# Example usage
if __name__ == "__main__":
    # Example reviews for testing
    sample_reviews = [
        {
            "author": "Will M",
            "rating": 5,
            "text": "By far the best dentist I've been to in America or Japan! I walked in to make an appointment for a cavity that was hurting, thinking they would make an appointment for a future date. They said they would see me that same day to take a look. Great service and English speaking staff.",
            "date": "2024-01-15"
        },
        {
            "author": "Sarah T",
            "rating": 5,
            "text": "Excellent cleaning service. The kids love coming here. Dr. Smith is very gentle and explains everything in English. Insurance was accepted without any issues. Modern equipment and very clean office.",
            "date": "2024-01-10"
        }
    ]
    
    analyze_provider_keywords("Womble Gate American Dentist", sample_reviews) 