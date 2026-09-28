import sys
import os
import unittest
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.api.knowledge import cosine_similarity
from app.core.router import classify_task

class TestPhase2(unittest.IsolatedAsyncioTestCase):
    def test_cosine_similarity(self):
        v1 = [1, 0, 0]
        v2 = [1, 0, 0]
        self.assertAlmostEqual(cosine_similarity(v1, v2), 1.0)
        
        v3 = [0, 1, 0]
        self.assertAlmostEqual(cosine_similarity(v1, v3), 0.0)
        
        # Test zero vectors
        self.assertEqual(cosine_similarity([0, 0], [1, 1]), 0.0)

    async def test_classify_task_chat(self):
        messages = [{"role": "user", "content": "Hello, how are you?"}]
        task_type = await classify_task(messages)
        self.assertEqual(task_type, "chat")

    async def test_classify_task_code_keyword(self):
        messages = [{"role": "user", "content": "Can you help me with this python script?"}]
        task_type = await classify_task(messages)
        self.assertEqual(task_type, "code")

if __name__ == "__main__":
    unittest.main()
