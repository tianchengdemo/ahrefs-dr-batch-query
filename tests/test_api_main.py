import unittest
from unittest.mock import patch

from fastapi import BackgroundTasks

from api import main as api_main


class QueryDomainTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        api_main.tasks_storage.clear()

    async def test_query_domain_returns_cached_result(self) -> None:
        cached_result = {
            "domain": "example.com",
            "domain_rating": 79,
            "ahrefs_rank": 12345,
        }

        with patch.object(api_main, "get_cached_domain_metrics", return_value=cached_result):
            response = await api_main.query_domain(
                api_main.QueryRequest(domain="example.com", country="us"),
                BackgroundTasks(),
            )

        self.assertEqual(response.status, "completed")
        self.assertEqual(response.message, "Result returned from cache")
        self.assertEqual(response.source, "cache")
        self.assertEqual(response.cached_domains, 1)
        self.assertEqual(response.live_domains, 0)
        self.assertIsNotNone(response.results)
        self.assertEqual(len(response.results), 1)
        self.assertEqual(response.results[0].domain, cached_result["domain"])
        self.assertEqual(response.results[0].domain_rating, float(cached_result["domain_rating"]))
        self.assertEqual(response.results[0].ahrefs_rank, cached_result["ahrefs_rank"])
        self.assertEqual(len(api_main.tasks_storage), 1)

    async def test_query_domain_fetches_live_result_synchronously_by_default(self) -> None:
        live_result = {
            "domain": "example.com",
            "domain_rating": 79,
            "ahrefs_rank": 12345,
        }
        background_tasks = BackgroundTasks()

        def complete_task(task_id: str, domains: list[str], country: str) -> None:
            api_main.tasks_storage[task_id]["status"] = "completed"
            api_main.tasks_storage[task_id]["results"] = [live_result]
            api_main.tasks_storage[task_id]["source"] = "live"
            api_main.tasks_storage[task_id]["cached_domains"] = 0
            api_main.tasks_storage[task_id]["live_domains"] = 1

        with patch.object(api_main, "get_cached_domain_metrics", return_value=None), patch.object(
            api_main, "process_query_task", side_effect=complete_task
        ) as process_query_task:
            response = await api_main.query_domain(
                api_main.QueryRequest(domain="example.com", country="us"),
                background_tasks,
            )

        self.assertEqual(response.status, "completed")
        self.assertEqual(response.message, "Result fetched live")
        self.assertEqual(response.source, "live")
        self.assertEqual(response.cached_domains, 0)
        self.assertEqual(response.live_domains, 1)
        self.assertIsNotNone(response.results)
        self.assertEqual(len(response.results), 1)
        self.assertEqual(response.results[0].domain, live_result["domain"])
        self.assertEqual(response.results[0].domain_rating, float(live_result["domain_rating"]))
        self.assertEqual(response.results[0].ahrefs_rank, live_result["ahrefs_rank"])
        self.assertEqual(len(background_tasks.tasks), 0)
        process_query_task.assert_called_once()

    async def test_query_domain_returns_pending_when_async_mode_enabled(self) -> None:
        background_tasks = BackgroundTasks()

        with patch.object(api_main, "get_cached_domain_metrics", return_value=None), patch.object(
            api_main, "process_query_task"
        ) as process_query_task:
            response = await api_main.query_domain(
                api_main.QueryRequest(domain="example.com", country="us", async_mode=True),
                background_tasks,
            )

        self.assertEqual(response.status, "pending")
        self.assertEqual(response.message, "Task created and processing")
        self.assertEqual(response.source, "live")
        self.assertEqual(response.cached_domains, 0)
        self.assertEqual(response.live_domains, 1)
        self.assertIsNone(response.results)
        self.assertEqual(len(background_tasks.tasks), 1)
        process_query_task.assert_not_called()


class QueryDomainsWithCacheTests(unittest.TestCase):
    def test_should_refresh_cookie_ignores_none_items(self) -> None:
        self.assertFalse(api_main.should_refresh_cookie([None]))
        self.assertTrue(
            api_main.should_refresh_cookie(
                [
                    None,
                    {"error": "403 forbidden"},
                ]
            )
        )

    def test_query_domains_with_cache_builds_error_result_when_upstream_omits_domain(self) -> None:
        fresh_results = [
            {
                "domain": "example.com",
                "domain_rating": 79,
                "ahrefs_rank": 12345,
            }
        ]

        with patch.object(api_main.result_cache, "prune_expired"), patch.object(
            api_main.result_cache, "set"
        ) as cache_set, patch.object(
            api_main, "get_cached_domain_metrics", side_effect=[None, None]
        ), patch.object(
            api_main, "fetch_fresh_results", return_value=fresh_results
        ):
            response = api_main.query_domains_with_cache(
                ["example.com", "missing.com"],
                "us",
            )

        self.assertEqual(response["source"], "live")
        self.assertEqual(response["cached_domains"], 0)
        self.assertEqual(response["live_domains"], 2)
        self.assertEqual(len(response["results"]), 2)
        self.assertEqual(response["results"][0]["domain"], "example.com")
        self.assertEqual(response["results"][1]["domain"], "missing.com")
        self.assertEqual(response["results"][1]["error"], "Upstream query returned no result")
        cache_set.assert_called_once()

    def test_query_domains_with_cache_builds_error_result_when_upstream_returns_none_item(self) -> None:
        fresh_results = [None]

        with patch.object(api_main.result_cache, "prune_expired"), patch.object(
            api_main.result_cache, "set"
        ) as cache_set, patch.object(
            api_main, "get_cached_domain_metrics", return_value=None
        ), patch.object(
            api_main, "fetch_fresh_results", return_value=fresh_results
        ):
            response = api_main.query_domains_with_cache(
                ["missing.com"],
                "us",
            )

        self.assertEqual(response["source"], "live")
        self.assertEqual(response["cached_domains"], 0)
        self.assertEqual(response["live_domains"], 1)
        self.assertEqual(len(response["results"]), 1)
        self.assertEqual(response["results"][0]["domain"], "missing.com")
        self.assertEqual(response["results"][0]["error"], "Upstream query returned no result")
        cache_set.assert_not_called()


if __name__ == "__main__":
    unittest.main()
