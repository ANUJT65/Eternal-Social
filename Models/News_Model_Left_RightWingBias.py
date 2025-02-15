import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import time
from urllib.parse import quote
import json
import re

class NewsAnalyzer:
    def __init__(self, api_key):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def detect_sensitive_topic(self, query: str) -> bool:
        """Detect if the query contains sensitive religious/communal terms."""
        sensitive_terms = [
            'hindu', 'muslim', 'sikh', 'christian', 'religion',
            'kills', 'killed', 'murder', 'attack', 'riot',
            'communal', 'violence', 'temple', 'mosque', 'church'
        ]
        return any(term in query.lower() for term in sensitive_terms)

    def swap_subjects(self, query: str) -> str:
        """Swap subjects in a query to check for bias."""
        swap_pairs = [
            ('hindu', 'muslim'),
            ('temple', 'mosque'),
            ('hindus', 'muslims')
        ]
        
        query_lower = query.lower()
        for term1, term2 in swap_pairs:
            if term1 in query_lower and term2 not in query_lower:
                return query.lower().replace(term1, term2)
            elif term2 in query_lower and term1 not in query_lower:
                return query_lower.replace(term2, term1)
        return query

    def scrape_opindia(self, query: str) -> list:
        """Scrape OpIndia for articles."""
        try:
            # First try the fact-check section
            url = f"https://www.opindia.com/tag/fact-check/?s={quote(query)}"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = []
            
            # Find article containers
            article_elements = soup.find_all('article', class_='jeg_post')
            
            # If no articles found in fact-check section, try general search
            if not article_elements:
                url = f"https://www.opindia.com/?s={quote(query)}"
                response = requests.get(url, headers=self.headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                article_elements = soup.find_all('article', class_='jeg_post')
            
            for article in article_elements[:3]:  # Limit to top 3 results
                title_elem = article.find('h3', class_='jeg_post_title')
                if title_elem and title_elem.a:
                    title = title_elem.a.text.strip()
                    link = title_elem.a['href']
                    excerpt = article.find('div', class_='jeg_post_excerpt')
                    excerpt = excerpt.text.strip() if excerpt else "No excerpt available"
                    
                    # Check if article is already in the list to avoid duplicates
                    if not any(a['link'] == link for a in articles):
                        articles.append({
                            'title': title,
                            'link': link,
                            'excerpt': excerpt,
                            'source': 'OpIndia'
                        })
            
            return articles
        except Exception as e:
            print(f"Error scraping OpIndia: {e}")
            return []

    def scrape_altnews(self, query: str) -> list:
        """Scrape AltNews for articles."""
        try:
            url = f"https://www.altnews.in/?s={quote(query)}"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = []
            
            # Find article containers
            for article in soup.find_all('article')[:3]:  # Limit to top 3 results
                title_elem = article.find('h2', class_='entry-title')
                if title_elem and title_elem.a:
                    title = title_elem.a.text.strip()
                    link = title_elem.a['href']
                    excerpt = article.find('div', class_='entry-content')
                    excerpt = excerpt.text.strip() if excerpt else "No excerpt available"
                    
                    # Check if article is already in the list to avoid duplicates
                    if not any(a['link'] == link for a in articles):
                        articles.append({
                            'title': title,
                            'link': link,
                            'excerpt': excerpt,
                            'source': 'AltNews'
                        })
            
            return articles
        except Exception as e:
            print(f"Error scraping AltNews: {e}")
            return []

    def generate_balanced_variations(self, base_query: str) -> list:
        """Generate balanced variations for sensitive topics."""
        prompt = f"""
        Generate 5 factual, neutral, and balanced search queries to fact-check news about "{base_query}".
        
        Requirements:
        1. Use objective, non-inflammatory language
        2. Focus on verifiable facts and events
        3. Avoid bias towards any community or group
        4. Include queries that look for different perspectives
        5. Use terms like "incident", "event", "situation" instead of emotionally charged words
        
        Format the output as a JSON list of exactly 5 strings.
        Example: ["query 1", "query 2", "query 3", "query 4", "query 5"]
        
        Important: Ensure queries maintain neutrality and equal scrutiny regardless of the groups involved.
        """
        
        try:
            # Generate initial variations
            response = self.model.generate_content(prompt)
            variations = json.loads(response.text)
            
            # If it's a sensitive topic, check for bias
            if self.detect_sensitive_topic(base_query):
                # Generate variations for swapped subjects
                swapped_query = self.swap_subjects(base_query)
                if swapped_query != base_query:
                    swapped_response = self.model.generate_content(
                        prompt.replace(base_query, swapped_query)
                    )
                    swapped_variations = json.loads(swapped_response.text)
                    
                    # Combine and balance variations from both sets
                    balanced_variations = []
                    for i in range(5):
                        if i % 2 == 0:
                            balanced_variations.append(variations[i])
                        else:
                            balanced_variations.append(swapped_variations[i])
                    
                    return balanced_variations
            
            return variations[:5]
        except Exception as e:
            print(f"Error generating variations: {e}")
            return [
                f"fact check {base_query}",
                f"verify news {base_query}",
                f"investigation {base_query}",
                f"detailed report {base_query}",
                f"evidence {base_query}"
            ]

    def _format_articles_for_prompt(self, articles: list) -> str:
        """Format articles for the Gemini prompt."""
        formatted = ""
        for i, article in enumerate(articles, 1):
            formatted += f"\nArticle {i}:\n"
            formatted += f"Title: {article['title']}\n"
            formatted += f"Excerpt: {article['excerpt']}\n"
            formatted += f"Source Link: {article['link']}\n"
        return formatted

    def analyze_with_gemini(self, opindia_articles: list, altnews_articles: list, query: str) -> str:
        """Analyze articles using Gemini AI with bias control."""
        prompt = f"""
        Act as an impartial fact-checker analyzing coverage of "{query}". Your role is to provide a completely neutral analysis without any bias towards any community, religion, or ideology.

        Guidelines for analysis:
        1. Use neutral language throughout
        2. Give equal weight to verifiable claims from all sides
        3. Focus on facts and evidence, not rhetoric
        4. Point out potential biases in ALL sources
        5. Treat all communities and groups with equal scrutiny
        6. Highlight missing context from both perspectives
        7. Separate facts from opinions in all sources

        OpIndia Articles:
        {self._format_articles_for_prompt(opindia_articles)}

        AltNews Articles:
        {self._format_articles_for_prompt(altnews_articles)}

        Provide analysis covering:
        1. Verifiable facts presented by each source
        2. Evidence and documentation provided
        3. Claims that require additional verification
        4. Missing context from both perspectives
        5. Potential biases in ALL sources
        6. Areas of agreement between sources
        7. Recommendations for further fact-checking

        Important: Maintain strict neutrality and apply equal scrutiny to all sources and claims.
        """

        try:
            response = self.model.generate_content(prompt)
            
            # Additional bias check for sensitive topics
            if self.detect_sensitive_topic(query):
                bias_check_prompt = f"""
                Review this analysis for any potential bias:
                {response.text}
                
                Check for:
                1. Equal scrutiny of all groups
                2. Neutral language throughout
                3. Fair treatment of all perspectives
                4. Balance in fact-checking claims
                
                If any bias is detected, provide a revised, neutral version.
                """
                
                final_response = self.model.generate_content(bias_check_prompt)
                return final_response.text
            
            return response.text
        except Exception as e:
            return f"Error in Gemini analysis: {e}"

    def analyze_topic(self, query: str):
        """Main function to analyze a topic with bias control."""
        print(f"\nAnalyzing topic: {query}")
        print("Generating balanced search variations...")
        
        search_variations = self.generate_balanced_variations(query)
        all_opindia_articles = []
        all_altnews_articles = []

        for variation in search_variations:
            print(f"\nSearching with variation: {variation}")
            
            opindia_results = self.scrape_opindia(variation)
            altnews_results = self.scrape_altnews(variation)
            
            all_opindia_articles.extend(opindia_results)
            all_altnews_articles.extend(altnews_results)
            
            time.sleep(2)

        print("\nPerforming balanced analysis...")
        analysis = self.analyze_with_gemini(all_opindia_articles, all_altnews_articles, query)
        
        return {
            'query': query,
            'search_variations': search_variations,
            'opindia_articles': all_opindia_articles,
            'altnews_articles': all_altnews_articles,
            'analysis': analysis
        }

def main():
    api_key = ""  # Replace with your actual API key
    analyzer = NewsAnalyzer(api_key)
    
    while True:
        query = input("\nEnter a topic to analyze (or 'quit' to exit): ")
        if query.lower() == 'quit':
            break
            
        results = analyzer.analyze_topic(query)
        
        print("\n=== BALANCED SEARCH VARIATIONS ===")
        for i, variation in enumerate(results['search_variations'], 1):
            print(f"{i}. {variation}")
            
        print("\n=== ARTICLES FOUND ===")
        print("\nOpIndia Articles:")
        for i, article in enumerate(results['opindia_articles'], 1):
            print(f"\n{i}. {article['title']}")
            print(f"   Link: {article['link']}")
            
        print("\nAltNews Articles:")
        for i, article in enumerate(results['altnews_articles'], 1):
            print(f"\n{i}. {article['title']}")
            print(f"   Link: {article['link']}")
            
        print("\n=== BALANCED ANALYSIS ===")
        print(results['analysis'])

if __name__ == "__main__":
    main()