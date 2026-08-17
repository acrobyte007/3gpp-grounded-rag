# app/services/keyword_extraction.py
import yake
from typing import List, Dict
from logger.logger import get_logger

logger = get_logger(__name__)


class KeywordExtractor:
    def __init__(self):
        self.extractor = None
        self._initialized = False

    def initialize(self):
        if self._initialized:
            return
        
        try:
            logger.info("Loading YAKE for keyword extraction...")
            self.extractor = yake.KeywordExtractor(
                lan="en",
                n=3,
                dedupLim=0.9,
                dedupFunc='seqm',
                windowsSize=1,
                top=50
            )
            self._initialized = True
            logger.info("Keyword extractor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize keyword extractor: {str(e)}")
            raise

    def extract_keywords(self, text: str) -> List[str]:
        if not self._initialized:
            self.initialize()
        
        try:
            keywords_with_scores = self.extractor.extract_keywords(text)
            keywords = [kw for kw, score in keywords_with_scores]
            logger.info(f"Extracted {len(keywords)} keywords")
            return keywords
        except Exception as e:
            logger.error(f"Failed to extract keywords: {str(e)}")
            return []

    def extract_keywords_with_score(self, text: str) -> List[Dict]:
        if not self._initialized:
            self.initialize()
        
        try:
            keywords_with_scores = self.extractor.extract_keywords(text)
            keywords = [
                {"keyword": kw, "score": score}
                for kw, score in keywords_with_scores
            ]
            logger.info(f"Extracted {len(keywords)} keywords with scores")
            return keywords
        except Exception as e:
            logger.error(f"Failed to extract keywords with scores: {str(e)}")
            return []

    def process_chunks(self, chunks: List[Dict]) -> List[Dict]:
        if not self._initialized:
            self.initialize()
        
        processed_chunks = []
        
        for chunk in chunks:
            text = chunk.get("text", "")
            if text:
                keywords = self.extract_keywords(text)
                chunk["keywords"] = keywords
            processed_chunks.append(chunk)
        
        logger.info(f"Processed {len(processed_chunks)} chunks with keywords")
        return processed_chunks


keyword_extractor = KeywordExtractor()