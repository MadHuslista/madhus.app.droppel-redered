"""Route smoke tests, automatically skipped until FastAPI test deps exist."""

from __future__ import annotations

import importlib.util
import unittest


HAS_ROUTE_TEST_DEPS = all(
    importlib.util.find_spec(name) is not None
    for name in ("fastapi", "httpx")
)


@unittest.skipUnless(HAS_ROUTE_TEST_DEPS, "FastAPI/httpx are not installed locally")
class Phase0RouteSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        from fastapi.testclient import TestClient

        from app.main import app

        self.client = TestClient(app)

    def test_healthz(self) -> None:
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()