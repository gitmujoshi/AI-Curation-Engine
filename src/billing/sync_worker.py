"""
Billing Sync Worker

Periodically syncs usage data from Redis to PostgreSQL and Stripe.
"""

import asyncio
import logging
from datetime import datetime
from typing import List

from src.gateway.config import settings

logger = logging.getLogger(__name__)


class BillingSync:
    """
    Background worker that syncs usage to billing systems.
    
    Runs every hour to:
    1. Flush Redis usage data to PostgreSQL
    2. Report usage to Stripe
    3. Reset Redis counters
    """
    
    def __init__(self, redis_client, db_client):
        self.redis_client = redis_client
        self.db_client = db_client
        self.interval = settings.BILLING_SYNC_INTERVAL_SECONDS
    
    async def sync_tenant_usage(self, tenant_id: str) -> None:
        """
        Sync usage for a single tenant.
        
        Args:
            tenant_id: Tenant identifier
        """
        try:
            # Get usage from Redis
            usage_key = f"usage:{tenant_id}"
            usage_data = await self.redis_client.hgetall(usage_key)
            
            if not usage_data:
                return
            
            tokens_saved = int(usage_data.get("tokens_saved", 0))
            requests = int(usage_data.get("requests", 0))
            
            # Store in PostgreSQL
            await self._store_usage_db(tenant_id, tokens_saved, requests)
            
            # Report to Stripe
            await self._report_to_stripe(tenant_id, tokens_saved)
            
            # Reset Redis counters
            await self.redis_client.delete(usage_key)
            
            logger.info(
                f"Synced usage for {tenant_id}: "
                f"{tokens_saved} tokens, {requests} requests"
            )
            
        except Exception as e:
            logger.error(f"Error syncing usage for {tenant_id}: {e}")
    
    async def _store_usage_db(
        self,
        tenant_id: str,
        tokens_saved: int,
        requests: int
    ) -> None:
        """Store usage in PostgreSQL."""
        # Placeholder - implement actual DB insert
        logger.debug(f"Storing usage in DB: {tenant_id}, {tokens_saved} tokens")
    
    async def _report_to_stripe(self, tenant_id: str, tokens_saved: int) -> None:
        """Report usage to Stripe."""
        if not settings.STRIPE_API_KEY:
            return
        
        try:
            # Placeholder - implement Stripe usage record creation
            # import stripe
            # stripe.SubscriptionItem.create_usage_record(
            #     subscription_item_id,
            #     quantity=tokens_saved,
            #     timestamp=int(datetime.utcnow().timestamp())
            # )
            logger.debug(f"Reported {tokens_saved} tokens to Stripe for {tenant_id}")
            
        except Exception as e:
            logger.error(f"Error reporting to Stripe: {e}")
    
    async def run(self) -> None:
        """Run the billing sync worker."""
        logger.info(f"Starting billing sync worker (interval: {self.interval}s)")
        
        while True:
            try:
                # Get all tenant IDs with usage data
                # In production, query from database
                tenant_ids = ["tenant_test_001"]  # Placeholder
                
                for tenant_id in tenant_ids:
                    await self.sync_tenant_usage(tenant_id)
                
                logger.info("Billing sync completed successfully")
                
            except Exception as e:
                logger.error(f"Error in billing sync: {e}")
            
            # Wait for next interval
            await asyncio.sleep(self.interval)
