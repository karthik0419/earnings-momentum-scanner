"""
Explore GitHub for best algo trading repositories
Find proven strategies for NSE options trading
"""

import requests
import json
from datetime import datetime

def search_github_repos(query, sort='stars', per_page=30):
    """Search GitHub repositories"""
    url = f"https://api.github.com/search/repositories"
    params = {
        'q': query,
        'sort': sort,
        'order': 'desc',
        'per_page': per_page
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def print_repos(repos, title):
    """Print repository list"""
    print("\n" + "="*100)
    print(f"🔍 {title}")
    print("="*100)
    
    if not repos or 'items' not in repos:
        print("No repositories found")
        return
    
    for i, repo in enumerate(repos['items'][:20], 1):
        name = repo['name']
        stars = repo['stargazers_count']
        forks = repo['forks_count']
        desc = repo['description'][:80] if repo['description'] else "No description"
        url = repo['html_url']
        language = repo['language'] or "N/A"
        updated = repo['updated_at'][:10]
        
        print(f"\n{i}. ⭐ {stars:,} | 🍴 {forks:,} | {language}")
        print(f"   📦 {name}")
        print(f"   📝 {desc}")
        print(f"   🔗 {url}")
        print(f"   📅 Updated: {updated}")

def analyze_top_repos():
    """Analyze top algo trading repos"""
    
    queries = [
        ("algo trading python options", "General Algo Trading (Options)"),
        ("algorithmic trading python india", "India-specific Algo Trading"),
        ("options trading strategy python", "Options Trading Strategies"),
        ("zerodha kite api python", "Zerodha Kite API Projects"),
        ("nse options trading python", "NSE Options Trading"),
        ("momentum trading python", "Momentum Trading Strategies"),
        ("backtesting python options", "Backtesting Frameworks"),
        ("quantitative trading python", "Quantitative Trading"),
    ]
    
    all_results = {}
    
    for query, title in queries:
        print(f"\n🔍 Searching: {query}...")
        repos = search_github_repos(query)
        all_results[title] = repos
        
        if repos:
            print(f"   ✅ Found {repos['total_count']:,} repositories")
    
    # Print results
    for title, repos in all_results.items():
        print_repos(repos, title)
    
    # Save to file
    with open('results/github_repos.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print("\n" + "="*100)
    print("💾 Results saved to results/github_repos.json")
    print("="*100)

def recommend_repos():
    """Recommend best repos for our use case"""
    print("\n" + "="*100)
    print("🎯 RECOMMENDED REPOSITORIES FOR NSE OPTIONS ALGO TRADING")
    print("="*100)
    
    recommendations = [
        {
            'name': 'freqtrade',
            'url': 'https://github.com/freqtrade/freqtrade',
            'stars': '25k+',
            'why': 'Most popular crypto trading bot, can be adapted for options',
            'pros': ['Well-tested', 'Active community', 'Good backtesting'],
            'cons': ['Crypto-focused', 'Needs adaptation for NSE']
        },
        {
            'name': 'zipline',
            'url': 'https://github.com/quantopian/zipline',
            'stars': '17k+',
            'why': 'Quantopian backtesting engine, industry-standard',
            'pros': ['Professional-grade', 'Excellent backtesting', 'Well-documented'],
            'cons': ['US markets focused', 'Complex setup']
        },
        {
            'name': 'backtrader',
            'url': 'https://github.com/mementum/backtrader',
            'stars': '13k+',
            'why': 'Python backtesting library, very flexible',
            'pros': ['Easy to use', 'Good for options', 'Active development'],
            'cons': ['Learning curve', 'Documentation could be better']
        },
        {
            'name': 'vnpy',
            'url': 'https://github.com/vnpy/vnpy',
            'stars': '23k+',
            'why': 'Full-featured trading platform, supports multiple brokers',
            'pros': ['Complete solution', 'Multi-broker', 'Live trading ready'],
            'cons': ['Chinese-focused', 'Heavy framework']
        },
        {
            'name': 'jesse',
            'url': 'https://github.com/jesse-ai/jesse',
            'stars': '5k+',
            'why': 'Advanced backtesting and live trading, modern Python',
            'pros': ['Modern codebase', 'Great backtesting', 'Good docs'],
            'cons': ['Crypto-focused', 'Newer project']
        },
        {
            'name': 'AlgoTrading (India-specific)',
            'url': 'https://github.com/topics/algo-trading-india',
            'stars': 'Various',
            'why': 'India-specific algo trading repos',
            'pros': ['NSE-focused', 'Zerodha integration', 'Local examples'],
            'cons': ['Smaller projects', 'Less maintained']
        }
    ]
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['name']} ({rec['stars']} stars)")
        print(f"   🔗 {rec['url']}")
        print(f"   💡 Why: {rec['why']}")
        print(f"   ✅ Pros: {', '.join(rec['pros'])}")
        print(f"   ⚠️  Cons: {', '.join(rec['cons'])}")
    
    print("\n" + "="*100)
    print("🎯 BEST CHOICE FOR YOU:")
    print("="*100)
    print("""
    For NSE Options Intraday Momentum Scalping:
    
    1. START WITH: backtrader
       - Easy to learn
       - Good for options
       - Can integrate with Zerodha API
       - Our mock_backtest.py is similar approach
    
    2. THEN ADD: Zerodha Kite Connect API
       - Official Zerodha API
       - Real-time data
       - Order execution
       - Free for clients
    
    3. OPTIONAL: freqtrade (for ideas)
       - Study their strategy structure
       - Learn from their backtesting
       - Adapt concepts for options
    
    4. BUILD YOUR OWN (recommended):
       - Use our mock_backtest.py as base
       - Add real NSE data
       - Integrate Zerodha API
       - Keep it simple and focused
    """)

if __name__ == "__main__":
    import os
    os.makedirs('results', exist_ok=True)
    
    print("\n🚀 EXPLORING GITHUB FOR ALGO TRADING REPOSITORIES")
    print("="*100)
    
    # Analyze repos
    analyze_top_repos()
    
    # Recommendations
    recommend_repos()
    
    print("\n✅ Exploration complete!")
