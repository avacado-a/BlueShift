import feedparser
import re
import logging
from collections import Counter

logger = logging.getLogger(__name__)

def clean_headline(text: str) -> str:
    """Cleans HTML tags, normalizes quotes, and strips source metadata from headlines."""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Normalize quotes/apostrophes
    text = text.replace('\u2019', "'").replace('\u2018', "'").replace('\u201d', '"').replace('\u201c', '"')
    text = text.replace('\ufffd', "'")
    
    # Split on common source separators (e.g., "Headline - Source Name")
    parts = re.split(r'\s+[\-\u2013\u2014|]\s+', text)
    if parts:
        return parts[0].strip()
    return text.strip()

def clean_summary_text(summary_html: str) -> list[str]:
    """Extracts and cleans all headlines embedded inside the Google News summary HTML."""
    if not summary_html:
        return []
    # Find all text inside href tags: <a ...>Text</a>
    sub_titles = re.findall(r'<a[^>]*>(.*?)</a>', summary_html)
    return [clean_headline(st) for st in sub_titles if st]

def fetch_trending_topics(num_topics: int = 8) -> list[str]:
    """Scrapes Google News RSS and extracts the top 5-10 trending topics based on phrase frequency."""
    feed_url = 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en'
    logger.info(f"Scraping top articles from RSS feed: {feed_url}")
    
    try:
        feed = feedparser.parse(feed_url)
    except Exception as e:
        logger.error(f"Failed to fetch RSS feed: {e}")
        # Fallback topics in case of network failure
        return ["Artificial Intelligence", "Climate Change", "Interest Rates", "Global Economy", "Ebola Outbreak"]

    if not feed.entries:
        logger.warning("No entries found in RSS feed. Returning fallback topics.")
        return ["Artificial Intelligence", "Climate Change", "Interest Rates", "Global Economy", "Ebola Outbreak"]

    headlines = []
    for entry in feed.entries:
        headlines.append(clean_headline(entry.title))
        summary_html = entry.get('summary', '')
        if summary_html:
            headlines.extend(clean_summary_text(summary_html))
            
    # Deduplicate headlines
    headlines = list(set(headlines))
    
    # Common words blacklist to prevent generic topics
    blacklist = {
        'the', 'a', 'an', 'and', 'or', 'but', 'if', 'for', 'at', 'by', 'to', 'in', 'on', 'with', 'new', 'old',
        'breaking', 'live', 'update', 'updates', 'video', 'watch', 'how', 'why', 'what', 'who', 'where', 'when',
        'is', 'are', 'was', 'were', 'be', 'been', 'has', 'have', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
        'can', 'could', 'may', 'might', 'must', 'about', 'over', 'after', 'before', 'under', 'between', 'among',
        'cnbc', 'reuters', 'ap', 'bloomberg', 'cnn', 'bbc', 'yahoo', 'forbes', 'fox', 'nbc', 'cbs', 'abc', 'nyt',
        'today', 'tonight', 'morning', 'daily', 'news', 'press', 'report', 'reports', 'say', 'says', 'said', 'state',
        'states', 'court', 'supreme', 'house', 'white', 'senate', 'congress', 'president', 'biden', 'trump', 'gop', 'democrats',
        'us', 'u.s.', 'uk', 'u.k.', 'eu', 'un', 'u.n.', 'world', 'first', 'one', 'two', 'three', 'years', 'year', 'day', 'days',
        'week', 'month', 'months', 'time', 'times', 'people', 'man', 'woman', 'police', 'city', 'officer', 'officers',
        'here', 'there', 'their', 'them', 'they', 'our', 'your', 'my', 'his', 'her', 'its', 'from', 'into', 'out', 'up', 'down'
    }

    candidates = []
    for hl in headlines:
        # Regex matching capitalized word sequences (Proper Nouns/Entities)
        matches = re.finditer(r'\b([A-Z][a-zA-Z0-9\'-]*(?:\s+[A-Z][a-zA-Z0-9\'-]*)*)\b', hl)
        for match in matches:
            phrase = match.group(1).strip()
            phrase = re.sub(r'^[^\w]+|[^\w]+$', '', phrase) # Clean outer punctuation
            
            words_in_phrase = [w.lower() for w in phrase.split()]
            if not words_in_phrase:
                continue
                
            # Skip if all words in the phrase are blacklisted
            if all(w in blacklist for w in words_in_phrase):
                continue
                
            # Strip common leading articles
            if words_in_phrase[0] in {'the', 'a', 'an'}:
                phrase = ' '.join(phrase.split()[1:])
                words_in_phrase = words_in_phrase[1:]
                
            if not phrase or len(phrase) < 3:
                continue
                
            # Discard if it's a single word that is in the blacklist
            if len(words_in_phrase) == 1 and words_in_phrase[0] in blacklist:
                continue
                
            # Clean inner quote structures
            phrase = phrase.replace("'", "").replace('"', "")
            
            if phrase.lower() in blacklist:
                continue
                
            candidates.append(phrase)

    counter = Counter(candidates)
    top_results = [topic for topic, count in counter.most_common(num_topics)]
    logger.info(f"Extracted trending topics: {top_results}")
    
    # Ensure we return at least a subset of topics
    if not top_results:
        return ["Artificial Intelligence", "Climate Change", "Interest Rates", "Global Economy", "Ebola Outbreak"]
        
    return top_results

def fetch_trending_topics_with_context(num_topics: int = 8) -> dict[str, list[str]]:
    """
    Scrapes Google News RSS, extracts top trending topics, and gathers matching headlines 
    for context. Returns a dict mapping topic -> list of matching headlines.
    """
    feed_url = 'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en'
    logger.info(f"Scraping top articles from RSS feed for context: {feed_url}")
    try:
        feed = feedparser.parse(feed_url)
    except Exception as e:
        logger.error(f"Failed to fetch RSS feed: {e}")
        return {t: [] for t in ["Artificial Intelligence", "Climate Change", "Interest Rates", "Global Economy", "Ebola Outbreak"]}

    if not feed.entries:
        return {t: [] for t in ["Artificial Intelligence", "Climate Change", "Interest Rates", "Global Economy", "Ebola Outbreak"]}

    headlines = []
    for entry in feed.entries:
        headlines.append(clean_headline(entry.title))
        summary_html = entry.get('summary', '')
        if summary_html:
            headlines.extend(clean_summary_text(summary_html))
    headlines = list(set(headlines))

    # Get the top topics first using the existing function
    top_topics = fetch_trending_topics(num_topics)

    context = {}
    for topic in top_topics:
        matching_headlines = []
        topic_lower = topic.lower()
        for hl in headlines:
            if topic_lower in hl.lower():
                matching_headlines.append(hl)
        context[topic] = matching_headlines[:5] # Limit context to 5 headlines

    return context

