"""
Amazon Image Agent - Main loop
Automated agent that monitors Amazon listings and generates product images using Krea AI
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add modules to path
sys.path.append(str(Path(__file__).parent))

from config.settings import (
    LOG_FILE, LOG_LEVEL, MAX_LISTINGS_PER_RUN, IMAGES_PER_LISTING
)
from modules.amazon_monitor import AmazonMonitor
from modules.krea_client import KreaClient
from modules.revenue_tracker import RevenueTracker

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class AmazonImageAgent:
    """Main agent orchestrator"""
    
    def __init__(self):
        """Initialize the agent"""
        logger.info("="*60)
        logger.info("Amazon Image Agent Starting")
        logger.info("="*60)
        
        self.monitor = AmazonMonitor()
        self.krea_client = KreaClient()
        self.revenue_tracker = RevenueTracker()
        
        logger.info("All modules initialized successfully")
    
    def run_cycle(self) -> Dict:
        """
        Run one cycle of the agent loop
        
        Returns:
            Summary dictionary with cycle results
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting new agent cycle at {datetime.now()}")
        logger.info(f"{'='*60}\n")
        
        results = {
            "cycle_start": datetime.now().isoformat(),
            "listings_processed": 0,
            "images_generated": 0,
            "errors": []
        }
        
        try:
            # Step 1: Get new listings that need images
            logger.info(f"Fetching new listings (max {MAX_LISTINGS_PER_RUN})...")
            listings = self.monitor.get_new_listings(max_count=MAX_LISTINGS_PER_RUN)
            
            if not listings:
                logger.info("No new listings found. Cycle complete.")
                return results
            
            logger.info(f"Found {len(listings)} new listings to process")
            
            # Step 2: Process each listing
            for listing in listings:
                try:
                    self._process_listing(listing, results)
                except Exception as e:
                    error_msg = f"Error processing {listing['asin']}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # Step 3: Summary
            logger.info(f"\n{'='*60}")
            logger.info("Cycle Summary:")
            logger.info(f"  Listings processed: {results['listings_processed']}")
            logger.info(f"  Images generated: {results['images_generated']}")
            logger.info(f"  Errors: {len(results['errors'])}")
            logger.info(f"{'='*60}\n")
            
        except Exception as e:
            error_msg = f"Critical error in agent cycle: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        results["cycle_end"] = datetime.now().isoformat()
        return results
    
    def _process_listing(self, listing: Dict, results: Dict) -> None:
        """
        Process a single listing: generate images and track
        
        Args:
            listing: Listing dictionary from AmazonMonitor
            results: Results dictionary to update
        """
        asin = listing["asin"]
        product_name = listing["title"]
        
        logger.info(f"\n--- Processing: {product_name} (ASIN: {asin}) ---")
        
        # Generate image prompts
        prompts = self.monitor.generate_image_prompts(listing)
        logger.info(f"Generated {len(prompts)} image prompts")
        
        # Limit to configured number of images
        prompts = prompts[:IMAGES_PER_LISTING]
        
        # Define styles for variety
        styles = ["realistic", "lifestyle", "realistic", "minimal", "realistic"][:len(prompts)]
        
        # Generate images
        logger.info(f"Generating {len(prompts)} images via Krea AI...")
        image_results = self.krea_client.generate_multiple_images(
            prompts=prompts,
            product_name=product_name,
            asin=asin,
            styles=styles
        )
        
        logger.info(f"Successfully generated {len(image_results)} images for {asin}")
        
        # Track in revenue system
        self.revenue_tracker.track_listing(
            asin=asin,
            product_name=product_name,
            images_generated=len(image_results)
        )
        
        # Mark as processed
        self.monitor.mark_as_processed(asin)
        
        # Update results
        results["listings_processed"] += 1
        results["images_generated"] += len(image_results)
        
        logger.info(f"✓ Completed processing for {asin}")
    
    def print_revenue_report(self, days: int = 30) -> None:
        """
        Print revenue performance report
        
        Args:
            days: Number of days to include in report
        """
        self.revenue_tracker.print_report(days=days)
    
    def get_top_performers(self, limit: int = 10) -> List[Dict]:
        """
        Get top performing listings
        
        Args:
            limit: Number of top listings to return
        
        Returns:
            List of performance dictionaries
        """
        return self.revenue_tracker.get_top_performers(limit=limit)


def main():
    """Main entry point"""
    agent = AmazonImageAgent()
    
    # Run one cycle
    results = agent.run_cycle()
    
    # Print revenue report
    agent.print_revenue_report(days=30)
    
    logger.info("Agent cycle complete")
    
    return results


if __name__ == "__main__":
    main()
