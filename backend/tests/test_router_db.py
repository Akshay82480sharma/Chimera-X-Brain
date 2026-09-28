import sys
import os
import asyncio
import unittest

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import init_db
from app.db.models import Provider, AIModel, Chat, Message
from app.core.config import settings

class TestBackendPhase1(unittest.IsolatedAsyncioTestCase):
    async def test_db_initialization(self):
        # Simply testing that models exist and init_db doesn't crash
        try:
            await init_db()
            db_ok = True
        except Exception as e:
            print(e)
            db_ok = False
            
        self.assertTrue(db_ok, "Database initialized successfully without schema errors")

    def test_routing_rules_exist(self):
        # Verify routing rules are correctly configured
        self.assertIn("auto", settings.routing_rules)
        self.assertIsInstance(settings.routing_rules.get("auto"), str)

if __name__ == "__main__":
    unittest.main()
