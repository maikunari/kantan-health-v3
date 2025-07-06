import requests
import json
import time
import csv
from datetime import datetime
from urllib.parse import quote_plus
import os
from pytrends.request import TrendReq
import pandas as pd
from bs4 import BeautifulSoup
import random

class KeywordResearchAutomation:
    def __init__(self):
        self.keywords = []
        self.competitor_data = []
        self.suggestions_data = []
        
        # Base healthcare terms
        self.base_terms = [
            "english doctor", "international clinic", "foreign friendly hospital",
            "expat doctor", "english speaking physician", "international medical center",
            "english hospital", "foreign doctor", "international dentist",
            "english speaking dentist", "expat clinic", "english pediatrician",
            "international pharmacy", "foreign friendly clinic", "english gynecologist",
            "expat medical care", "english cardiologist", "international dermatologist",
            "english orthopedic", "foreign eye doctor", "english psychiatrist",
            "international veterinarian", "english chiropractor", "expat dentist",
            "foreign medical center"
        ]
        
        # Top 25 Japanese cities with high foreign populations and English support
        # Based on research data from official sources and expat communities
        self.cities = [
            # Major metropolitan areas with highest foreign populations
            "tokyo", "osaka", "yokohama", "kyoto", "kobe", "fukuoka", "sapporo",
            "hiroshima", "sendai", "chiba", "kawasaki", "saitama", "kitakyushu",
            
            # Cities with significant expat communities and English support
            "nagoya", "nara", "kanazawa", "matsuyama", "okayama", "kumamoto",
            "niigata", "hamamatsu", "kagoshima", "miyazaki", "nagasaki", "oita"
        ]
        
        # Healthcare specialties
        self.specialties = [
            "general practice", "family medicine", "internal medicine", "pediatrics",
            "gynecology", "obstetrics", "dermatology", "ophthalmology", "dentistry",
            "orthopedics", "cardiology", "neurology", "psychiatry", "emergency medicine",
            "radiology", "anesthesiology", "surgery", "oncology", "urology",
            "gastroenterology", "endocrinology", "rheumatology", "infectious disease",
            "pulmonology", "nephrology", "plastic surgery", "ENT", "podiatry",
            "chiropractic", "physical therapy", "mental health", "women's health",
            "men's health", "children's health", "elderly care", "pharmacy",
            "vaccination", "health check", "medical tourism", "emergency care"
        ]
        
        # Commercial intent modifiers
        self.commercial_modifiers = [
            "find", "search", "locate", "near me", "appointment", "booking",
            "directory", "list", "recommended", "best", "top", "review",
            "cost", "price", "insurance", "contact", "phone", "address",
            "hours", "open", "emergency", "urgent", "consultation", "visit"
        ]
        
        # Location modifiers
        self.location_modifiers = [
            "near", "in", "around", "close to", "nearby", "central", "downtown",
            "station", "area", "district", "ward", "city", "prefecture"
        ]

    def generate_keyword_combinations(self):
        """Generate comprehensive keyword combinations"""
        combinations = []
        
        # Base term + city combinations
        for base_term in self.base_terms:
            for city in self.cities:
                combinations.append(f"{base_term} {city}")
                combinations.append(f"{base_term} in {city}")
                combinations.append(f"{city} {base_term}")
                
        # Specialty + city combinations
        for specialty in self.specialties:
            for city in self.cities:
                combinations.append(f"english {specialty} {city}")
                combinations.append(f"{specialty} doctor {city}")
                combinations.append(f"international {specialty} {city}")
                combinations.append(f"{city} english {specialty}")
                
        # Commercial intent combinations
        for modifier in self.commercial_modifiers:
            for city in self.cities:
                combinations.append(f"{modifier} english doctor {city}")
                combinations.append(f"{modifier} international clinic {city}")
                combinations.append(f"{modifier} expat doctor {city}")
                
        # Location-specific combinations
        for location_mod in self.location_modifiers:
            for city in self.cities:
                combinations.append(f"english doctor {location_mod} {city}")
                combinations.append(f"international clinic {location_mod} {city}")
                
        # Remove duplicates and sort
        combinations = list(set(combinations))
        combinations.sort()
        
        return combinations

    def get_google_suggestions(self, query, max_suggestions=10):
        """Get Google autocomplete suggestions"""
        try:
            url = "http://suggestqueries.google.com/complete/search"
            params = {
                'client': 'firefox',
                'q': query,
                'hl': 'en'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                suggestions = response.json()[1]
                return suggestions[:max_suggestions]
            else:
                return []
                
        except Exception as e:
            print(f"Error getting suggestions for '{query}': {str(e)}")
            return []

    def get_related_searches(self, base_queries, max_per_query=5):
        """Get related searches for base queries"""
        all_suggestions = []
        
        print("🔍 Gathering Google autocomplete suggestions...")
        
        for i, query in enumerate(base_queries[:20]):  # Limit to avoid rate limiting
            print(f"   Processing: {query} ({i+1}/{min(20, len(base_queries))})")
            
            suggestions = self.get_google_suggestions(query, max_per_query)
            
            for suggestion in suggestions:
                suggestion_data = {
                    'original_query': query,
                    'suggestion': suggestion,
                    'source': 'google_autocomplete'
                }
                all_suggestions.append(suggestion_data)
                
            # Rate limiting
            time.sleep(0.5)
            
        return all_suggestions

    def get_trends_data(self, keywords_sample, timeframe='today 12-m'):
        """Get Google Trends data for keyword sample"""
        trends_data = []
        
        try:
            print("📈 Analyzing Google Trends data...")
            pytrends = TrendReq(hl='en-US', tz=360)
            
            # Process keywords in batches of 5 (Google Trends limit)
            keyword_batches = [keywords_sample[i:i+5] for i in range(0, len(keywords_sample), 5)]
            
            for batch_num, batch in enumerate(keyword_batches[:5]):  # Limit batches
                print(f"   Processing trends batch {batch_num + 1}/5")
                
                try:
                    pytrends.build_payload(batch, cat=0, timeframe=timeframe, geo='JP')
                    interest_data = pytrends.interest_over_time()
                    
                    if not interest_data.empty:
                        for keyword in batch:
                            if keyword in interest_data.columns:
                                avg_interest = interest_data[keyword].mean()
                                trends_data.append({
                                    'keyword': keyword,
                                    'average_interest': avg_interest,
                                    'peak_interest': interest_data[keyword].max(),
                                    'source': 'google_trends'
                                })
                    
                    # Rate limiting
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"     Skipping batch due to error: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Error with trends analysis: {str(e)}")
            
        return trends_data

    def score_keywords(self, keywords, suggestions_data, trends_data):
        """Score keywords based on relevance and commercial potential"""
        scored_keywords = []
        
        # Create lookup dictionaries
        suggestions_dict = {item['suggestion']: item for item in suggestions_data}
        trends_dict = {item['keyword']: item for item in trends_data}
        
        for keyword in keywords:
            score = 0
            factors = []
            
            # Base scoring factors
            if any(commercial in keyword.lower() for commercial in 
                   ['find', 'search', 'appointment', 'booking', 'directory', 'near me']):
                score += 3
                factors.append("Commercial intent")
                
            if any(urgent in keyword.lower() for urgent in 
                   ['emergency', 'urgent', 'now', 'today']):
                score += 2
                factors.append("Urgency")
                
            if any(city in keyword.lower() for city in 
                   ['tokyo', 'osaka', 'yokohama', 'kyoto', 'fukuoka']):
                score += 2
                factors.append("Major city")
                
            if 'english' in keyword.lower():
                score += 2
                factors.append("English focus")
                
            if any(specialty in keyword.lower() for specialty in 
                   ['doctor', 'clinic', 'hospital', 'dentist', 'pharmacy']):
                score += 1
                factors.append("Healthcare term")
                
            # Google suggestions bonus
            if keyword in suggestions_dict:
                score += 1
                factors.append("Google suggestion")
                
            # Trends data bonus
            if keyword in trends_dict:
                trend_score = trends_dict[keyword]['average_interest']
                if trend_score > 50:
                    score += 2
                    factors.append("High search volume")
                elif trend_score > 20:
                    score += 1
                    factors.append("Medium search volume")
                    
            scored_keywords.append({
                'keyword': keyword,
                'score': score,
                'factors': factors,
                'estimated_difficulty': 'Low' if score <= 3 else 'Medium' if score <= 6 else 'High'
            })
            
        # Sort by score (highest first)
        scored_keywords.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_keywords

    def export_results(self, scored_keywords, suggestions_data, trends_data):
        """Export all results to organized files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create results directory
        results_dir = f"keyword_research_results_{timestamp}"
        os.makedirs(results_dir, exist_ok=True)
        
        # 1. Main keyword report (CSV)
        csv_file = os.path.join(results_dir, "keywords_ranked.csv")
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Keyword', 'Score', 'Difficulty', 'Ranking Factors'])
            
            for item in scored_keywords:
                writer.writerow([
                    item['keyword'],
                    item['score'],
                    item['estimated_difficulty'],
                    '; '.join(item['factors'])
                ])
        
        # 2. Google suggestions (CSV)
        suggestions_file = os.path.join(results_dir, "google_suggestions.csv")
        with open(suggestions_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Original Query', 'Suggestion', 'Source'])
            
            for item in suggestions_data:
                writer.writerow([
                    item['original_query'],
                    item['suggestion'],
                    item['source']
                ])
        
        # 3. Trends data (CSV)
        if trends_data:
            trends_file = os.path.join(results_dir, "trends_data.csv")
            with open(trends_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Keyword', 'Average Interest', 'Peak Interest', 'Source'])
                
                for item in trends_data:
                    writer.writerow([
                        item['keyword'],
                        item['average_interest'],
                        item['peak_interest'],
                        item['source']
                    ])
        
        # 4. Summary report (TXT)
        summary_file = os.path.join(results_dir, "research_summary.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("HEALTHCARE DIRECTORY KEYWORD RESEARCH SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"TOTAL KEYWORDS ANALYZED: {len(scored_keywords)}\n")
            f.write(f"GOOGLE SUGGESTIONS COLLECTED: {len(suggestions_data)}\n")
            f.write(f"TRENDS DATA POINTS: {len(trends_data)}\n\n")
            
            f.write("TOP 20 HIGH-OPPORTUNITY KEYWORDS:\n")
            f.write("-" * 40 + "\n")
            for i, item in enumerate(scored_keywords[:20], 1):
                f.write(f"{i:2d}. {item['keyword']} (Score: {item['score']})\n")
                f.write(f"    Factors: {', '.join(item['factors'])}\n\n")
            
            f.write("PRIORITY CITIES FOR DATA COLLECTION:\n")
            f.write("-" * 40 + "\n")
            city_mentions = {}
            for item in scored_keywords[:50]:  # Top 50 keywords
                for city in self.cities:
                    if city in item['keyword'].lower():
                        city_mentions[city] = city_mentions.get(city, 0) + 1
            
            sorted_cities = sorted(city_mentions.items(), key=lambda x: x[1], reverse=True)
            for i, (city, count) in enumerate(sorted_cities[:10], 1):
                f.write(f"{i:2d}. {city.title()} (mentioned in {count} high-value keywords)\n")
            
            f.write(f"\n\nRECOMMENDATIONS:\n")
            f.write("-" * 40 + "\n")
            f.write("1. Start data collection with Tokyo, Osaka, and Yokohama\n")
            f.write("2. Focus on 'english doctor' and 'international clinic' terms\n")
            f.write("3. Prioritize commercial intent keywords for SEO\n")
            f.write("4. Target specific specialties in major cities\n")
            f.write("5. Create location-specific landing pages\n")
        
        return results_dir

    def run_full_research(self):
        """Run the complete keyword research process"""
        print("🚀 Starting Healthcare Directory Keyword Research")
        print("=" * 60)
        
        # Step 1: Generate base keyword combinations
        print("\n📝 Step 1: Generating keyword combinations...")
        all_keywords = self.generate_keyword_combinations()
        print(f"   Generated {len(all_keywords)} keyword combinations")
        
        # Step 2: Get Google suggestions
        print("\n🔍 Step 2: Collecting Google autocomplete data...")
        sample_queries = all_keywords[:50]  # Sample for suggestions
        suggestions_data = self.get_related_searches(sample_queries)
        print(f"   Collected {len(suggestions_data)} suggestions")
        
        # Step 3: Get trends data  
        print("\n📈 Step 3: Analyzing search trends...")
        trends_sample = all_keywords[:25]  # Smaller sample for trends
        trends_data = self.get_trends_data(trends_sample)
        print(f"   Analyzed trends for {len(trends_data)} keywords")
        
        # Step 4: Score all keywords
        print("\n🎯 Step 4: Scoring and ranking keywords...")
        scored_keywords = self.score_keywords(all_keywords, suggestions_data, trends_data)
        print(f"   Scored {len(scored_keywords)} keywords")
        
        # Step 5: Export results
        print("\n💾 Step 5: Exporting results...")
        results_dir = self.export_results(scored_keywords, suggestions_data, trends_data)
        print(f"   Results saved to: {results_dir}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("✅ KEYWORD RESEARCH COMPLETE!")
        print("=" * 60)
        print(f"📊 Total keywords generated: {len(all_keywords)}")
        print(f"🔍 Google suggestions: {len(suggestions_data)}")
        print(f"📈 Trends data points: {len(trends_data)}")
        print(f"💾 Results exported to: {results_dir}")
        
        print(f"\n🎯 TOP 10 RECOMMENDED KEYWORDS:")
        for i, item in enumerate(scored_keywords[:10], 1):
            print(f"   {i:2d}. {item['keyword']} (Score: {item['score']})")
        
        print(f"\n🏙️  PRIORITY CITIES TO TARGET FIRST:")
        city_scores = {}
        for item in scored_keywords[:30]:
            for city in self.cities:
                if city in item['keyword'].lower():
                    city_scores[city] = city_scores.get(city, 0) + item['score']
        
        top_cities = sorted(city_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (city, score) in enumerate(top_cities, 1):
            print(f"   {i}. {city.title()} (Total score: {score})")
        
        return results_dir, scored_keywords

if __name__ == "__main__":
    researcher = KeywordResearchAutomation()
    researcher.run_full_research() 