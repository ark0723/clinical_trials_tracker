import httpx
import pytest
import respx

from app.infrastructure.ctgov_client import ClinicalTrialsGovClient

BASE_URL = "https://clinicaltrials.gov/api/v2"


@respx.mock
def test_search_studies_returns_studies_from_a_single_page():
    respx.get(f"{BASE_URL}/studies").mock(
        return_value=httpx.Response(
            200,
            json={
                "studies": [{"protocolSection": {"identificationModule": {"nctId": "NCT001"}}}],
                "totalCount": 1,
            },
        )
    )
    client = ClinicalTrialsGovClient(base_url=BASE_URL)

    studies = list(client.search_studies(condition="HER2-positive breast cancer"))

    assert len(studies) == 1
    assert studies[0]["protocolSection"]["identificationModule"]["nctId"] == "NCT001"


@respx.mock
def test_search_studies_follows_pagination_until_no_next_page_token():
    route = respx.get(f"{BASE_URL}/studies")
    route.side_effect = [
        httpx.Response(
            200,
            json={
                "studies": [{"protocolSection": {"identificationModule": {"nctId": "NCT001"}}}],
                "nextPageToken": "page-2",
            },
        ),
        httpx.Response(
            200,
            json={
                "studies": [{"protocolSection": {"identificationModule": {"nctId": "NCT002"}}}],
            },
        ),
    ]
    client = ClinicalTrialsGovClient(base_url=BASE_URL)

    studies = list(client.search_studies(condition="HER2-positive breast cancer"))

    nct_ids = [s["protocolSection"]["identificationModule"]["nctId"] for s in studies]
    assert nct_ids == ["NCT001", "NCT002"]
    assert route.call_count == 2
    second_request_params = route.calls[1].request.url.params
    assert second_request_params["pageToken"] == "page-2"


@respx.mock
def test_search_studies_sends_condition_and_status_filters():
    route = respx.get(f"{BASE_URL}/studies").mock(
        return_value=httpx.Response(200, json={"studies": []})
    )
    client = ClinicalTrialsGovClient(base_url=BASE_URL)

    list(
        client.search_studies(
            condition="HER2-positive breast cancer",
            statuses=["RECRUITING", "NOT_YET_RECRUITING"],
        )
    )

    sent_params = route.calls[0].request.url.params
    assert sent_params["query.cond"] == "HER2-positive breast cancer"
    assert sent_params["filter.overallStatus"] == "RECRUITING,NOT_YET_RECRUITING"


@respx.mock
def test_search_studies_retries_on_429_then_succeeds():
    route = respx.get(f"{BASE_URL}/studies")
    route.side_effect = [
        httpx.Response(429, headers={"Retry-After": "1"}),
        httpx.Response(200, json={"studies": [{"protocolSection": {}}]}),
    ]
    sleep_calls: list[float] = []
    client = ClinicalTrialsGovClient(
        base_url=BASE_URL, max_retries=3, sleep=sleep_calls.append
    )

    studies = list(client.search_studies(condition="HER2-positive breast cancer"))

    assert len(studies) == 1
    assert route.call_count == 2
    assert sleep_calls == [1.0]


@respx.mock
def test_search_studies_retries_on_server_error_with_exponential_backoff():
    route = respx.get(f"{BASE_URL}/studies")
    route.side_effect = [
        httpx.Response(503),
        httpx.Response(503),
        httpx.Response(200, json={"studies": []}),
    ]
    sleep_calls: list[float] = []
    client = ClinicalTrialsGovClient(
        base_url=BASE_URL, max_retries=3, backoff_seconds=2.0, sleep=sleep_calls.append
    )

    list(client.search_studies(condition="HER2-positive breast cancer"))

    assert route.call_count == 3
    assert sleep_calls == [2.0, 4.0]


@respx.mock
def test_search_studies_gives_up_after_max_retries():
    respx.get(f"{BASE_URL}/studies").mock(return_value=httpx.Response(429))
    client = ClinicalTrialsGovClient(base_url=BASE_URL, max_retries=2, sleep=lambda _: None)

    with pytest.raises(httpx.HTTPStatusError):
        list(client.search_studies(condition="HER2-positive breast cancer"))


@respx.mock
def test_search_studies_does_not_retry_on_client_errors_other_than_429():
    respx.get(f"{BASE_URL}/studies").mock(return_value=httpx.Response(400))
    client = ClinicalTrialsGovClient(base_url=BASE_URL, max_retries=3, sleep=lambda _: None)

    with pytest.raises(httpx.HTTPStatusError):
        list(client.search_studies(condition="HER2-positive breast cancer"))
