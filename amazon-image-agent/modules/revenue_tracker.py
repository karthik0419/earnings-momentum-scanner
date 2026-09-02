"""
Revenue tracking and analytics module
Tracks conversion rates, sales, and ROI from generated images
"""
import logging
import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import REVENUE_LOG, CONVERSION_RATE_TARGET, AVG_ORDER_VALUE_TARGET

logger = logging.getLogger(__name__)


class RevenueTracker:
    """Track revenue and performance metrics for image-enhanced listings"""
    
    def __init__(self):
        """Initialize revenue tracker"""
        self.revenue_log = REVENUE_LOG
        self.data = self._load_data()
        
        logger.info("RevenueTracker initialized")
    
    def _load_data(self) -> Dict:
        """Load revenue data from disk"""
        if not self.revenue_log.exists():
            return {
                "listings": {},
                "summary": {
                    "total_revenue": 0,
                    "total_orders": 0,
                    "total_listings_processed": 0,
                    "avg_conversion_rate": 0,
                    "avg_order_value": 0
                }
            }
        
        try:
            with open(self.revenue_log, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading revenue data: {e}")
            return {"listings": {}, "summary": {}}
    
    def _save_data(self) -> None:
        """Save revenue data to disk"""
        with open(self.revenue_log, "w") as f:
            json.dump(self.data, f, indent=2)
        
        logger.info("Revenue data saved")
    
    def track_listing(
        self,
        asin: str,
        product_name: str,
        images_generated: int,
        generation_date: Optional[str] = None
    ) -> None:
        """
        Start tracking a listing after image generation
        
        Args:
            asin: Amazon ASIN
            product_name: Product name
            images_generated: Number of images generated
            generation_date: ISO format date (defaults to now)
        """
        if generation_date is None:
            generation_date = datetime.now().isoformat()
        
        self.data["listings"][asin] = {
            "product_name": product_name,
            "images_generated": images_generated,
            "generation_date": generation_date,
            "orders": [],
            "total_revenue": 0,
            "total_orders": 0,
            "views": 0,
            "conversion_rate": 0
        }
        
        self.data["summary"]["total_listings_processed"] += 1
        self._save_data()
        
        logger.info(f"Started tracking ASIN {asin}")
    
    def record_order(
        self,
        asin: str,
        order_value: float,
        order_date: Optional[str] = None
    ) -> None:
        """
        Record an order for a tracked listing
        
        Args:
            asin: Amazon ASIN
            order_value: Order value in currency units
            order_date: ISO format date (defaults to now)
        """
        if asin not in self.data["listings"]:
            logger.warning(f"ASIN {asin} not tracked, cannot record order")
            return
        
        if order_date is None:
            order_date = datetime.now().isoformat()
        
        order = {
            "value": order_value,
            "date": order_date
        }
        
        listing = self.data["listings"][asin]
        listing["orders"].append(order)
        listing["total_revenue"] += order_value
        listing["total_orders"] += 1
        
        # Update conversion rate if we have views data
        if listing["views"] > 0:
            listing["conversion_rate"] = listing["total_orders"] / listing["views"]
        
        # Update summary
        self.data["summary"]["total_revenue"] += order_value
        self.data["summary"]["total_orders"] += 1
        
        self._save_data()
        
        logger.info(f"Recorded order for {asin}: Rs {order_value}")
    
    def update_views(self, asin: str, views: int) -> None:
        """
        Update view count for a listing
        
        Args:
            asin: Amazon ASIN
            views: Total view count
        """
        if asin not in self.data["listings"]:
            logger.warning(f"ASIN {asin} not tracked")
            return
        
        listing = self.data["listings"][asin]
        listing["views"] = views
        
        # Recalculate conversion rate
        if views > 0:
            listing["conversion_rate"] = listing["total_orders"] / views
        
        self._save_data()
    
    def get_listing_performance(self, asin: str) -> Optional[Dict]:
        """
        Get performance metrics for a specific listing
        
        Args:
            asin: Amazon ASIN
        
        Returns:
            Performance dictionary or None if not tracked
        """
        if asin not in self.data["listings"]:
            return None
        
        listing = self.data["listings"][asin]
        
        # Calculate days since image generation
        gen_date = datetime.fromisoformat(listing["generation_date"])
        days_active = (datetime.now() - gen_date).days
        
        # Calculate average order value
        avg_order_value = 0
        if listing["total_orders"] > 0:
            avg_order_value = listing["total_revenue"] / listing["total_orders"]
        
        return {
            "asin": asin,
            "product_name": listing["product_name"],
            "days_active": days_active,
            "total_revenue": listing["total_revenue"],
            "total_orders": listing["total_orders"],
            "avg_order_value": avg_order_value,
            "views": listing["views"],
            "conversion_rate": listing["conversion_rate"],
            "images_generated": listing["images_generated"]
        }
    
    def get_summary_report(self, days: Optional[int] = None) -> Dict:
        """
        Get summary performance report
        
        Args:
            days: Filter to last N days (None for all time)
        
        Returns:
            Summary report dictionary
        """
        summary = self.data["summary"].copy()
        
        if days is not None:
            # Filter to recent listings
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_listings = {
                asin: listing
                for asin, listing in self.data["listings"].items()
                if datetime.fromisoformat(listing["generation_date"]) >= cutoff_date
            }
            
            # Recalculate summary for filtered data
            summary["total_revenue"] = sum(l["total_revenue"] for l in recent_listings.values())
            summary["total_orders"] = sum(l["total_orders"] for l in recent_listings.values())
            summary["total_listings_processed"] = len(recent_listings)
        
        # Calculate averages
        if summary["total_listings_processed"] > 0:
            total_views = sum(l["views"] for l in self.data["listings"].values())
            if total_views > 0:
                summary["avg_conversion_rate"] = summary["total_orders"] / total_views
        
        if summary["total_orders"] > 0:
            summary["avg_order_value"] = summary["total_revenue"] / summary["total_orders"]
        
        # Add targets and performance vs targets
        summary["conversion_rate_target"] = CONVERSION_RATE_TARGET
        summary["avg_order_value_target"] = AVG_ORDER_VALUE_TARGET
        
        if summary["avg_conversion_rate"] > 0:
            summary["conversion_rate_vs_target"] = (
                summary["avg_conversion_rate"] / CONVERSION_RATE_TARGET
            )
        
        if summary["avg_order_value"] > 0:
            summary["avg_order_value_vs_target"] = (
                summary["avg_order_value"] / AVG_ORDER_VALUE_TARGET
            )
        
        return summary
    
    def get_top_performers(self, limit: int = 10) -> List[Dict]:
        """
        Get top performing listings by revenue
        
        Args:
            limit: Number of top listings to return
        
        Returns:
            List of listing performance dictionaries
        """
        performances = [
            self.get_listing_performance(asin)
            for asin in self.data["listings"].keys()
        ]
        
        # Sort by revenue
        performances.sort(key=lambda x: x["total_revenue"], reverse=True)
        
        return performances[:limit]
    
    def print_report(self, days: Optional[int] = None) -> None:
        """
        Print a formatted performance report
        
        Args:
            days: Filter to last N days (None for all time)
        """
        summary = self.get_summary_report(days)
        
        period = f"Last {days} days" if days else "All time"
        
        print(f"\n{'='*60}")
        print(f"Revenue Report - {period}")
        print(f"{'='*60}")
        print(f"Total Listings Processed: {summary['total_listings_processed']}")
        print(f"Total Orders: {summary['total_orders']}")
        print(f"Total Revenue: Rs {summary['total_revenue']:,.2f}")
        print(f"Avg Order Value: Rs {summary.get('avg_order_value', 0):,.2f}")
        print(f"Avg Conversion Rate: {summary.get('avg_conversion_rate', 0)*100:.2f}%")
        print(f"\nTargets:")
        print(f"  Conversion Rate Target: {CONVERSION_RATE_TARGET*100:.2f}%")
        print(f"  Avg Order Value Target: Rs {AVG_ORDER_VALUE_TARGET:,.2f}")
        
        if summary.get('conversion_rate_vs_target'):
            print(f"\nPerformance vs Targets:")
            print(f"  Conversion Rate: {summary['conversion_rate_vs_target']*100:.1f}% of target")
        
        if summary.get('avg_order_value_vs_target'):
            print(f"  Avg Order Value: {summary['avg_order_value_vs_target']*100:.1f}% of target")
        
        print(f"\n{'='*60}\n")


if __name__ == "__main__":
    # Test the tracker
    tracker = RevenueTracker()
    
    # Track a test listing
    tracker.track_listing(
        asin="B08TEST001",
        product_name="Test Product",
        images_generated=5
    )
    
    # Simulate some orders
    tracker.update_views("B08TEST001", 1000)
    tracker.record_order("B08TEST001", 2999)
    tracker.record_order("B08TEST001", 2999)
    tracker.record_order("B08TEST001", 2999)
    
    # Print report
    tracker.print_report()
