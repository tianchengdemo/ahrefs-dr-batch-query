import unittest
from unittest.mock import Mock

from ahrefs import AhrefsClient


class AhrefsClientTests(unittest.TestCase):
    def test_get_domain_rating_handles_null_metric_objects(self) -> None:
        client = AhrefsClient(cookie_header="test-cookie")
        response = Mock()
        response.status_code = 200
        response.json.return_value = [
            "Ok",
            {
                "domainRating": None,
                "ahrefsRank": None,
            },
        ]
        response.raise_for_status.return_value = None
        client.session.get = Mock(return_value=response)

        result = client.get_domain_rating("example.com", country="us")

        self.assertEqual(result["domain"], "example.com")
        self.assertIsNone(result["domain_rating"])
        self.assertIsNone(result["ahrefs_rank"])
        self.assertNotIn("error", result)


if __name__ == "__main__":
    unittest.main()
