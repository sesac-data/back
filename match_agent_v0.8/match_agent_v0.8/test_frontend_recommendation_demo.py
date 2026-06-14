from pathlib import Path


FRONTEND_SRC = Path(__file__).parent / "frontend" / "src"


def read_frontend_file(
    relative_path
):

    return (
        FRONTEND_SRC
        / relative_path
    ).read_text(
        encoding="utf-8"
    )


def test_recommendation_demo_uses_service_layer():

    app_source = read_frontend_file(
        "App.jsx"
    )

    assert "fetchGeneralCompanyRecommendationDemo" in app_source
    assert "mockRecommendationAdapter" not in app_source


def test_mock_adapter_contains_valid_and_rejected_combinations():

    adapter_source = read_frontend_file(
        "services/mockRecommendationAdapter.js"
    )

    assert "summarized_combinations" in adapter_source
    assert "rejected_combinations" in adapter_source
    assert "mutually_exclusive" in adapter_source
    assert "requires" in adapter_source


def test_service_can_select_api_adapter_without_removing_mock():

    service_source = read_frontend_file(
        "services/recommendationService.js"
    )

    assert "VITE_RECOMMENDATION_ADAPTER" in service_source
    assert "fetchApiRecommendationDemo" in service_source
    assert "fetchMockRecommendationDemo" in service_source


def test_demo_displays_null_amount_as_not_calculable():

    app_source = read_frontend_file(
        "App.jsx"
    )
    adapter_source = read_frontend_file(
        "services/mockRecommendationAdapter.js"
    )

    assert "계산 불가" in app_source
    assert "estimated_total_amount: null" in adapter_source


def test_evidence_snippets_are_exposed_in_demo_detail():

    app_source = read_frontend_file(
        "App.jsx"
    )

    assert "evidence_snippets" in app_source
    assert "formatJson(policyResult.evidence_snippets)" in app_source


def test_forbidden_best_recommendation_phrase_is_not_rendered():

    app_source = read_frontend_file(
        "App.jsx"
    )
    adapter_source = read_frontend_file(
        "services/mockRecommendationAdapter.js"
    )

    assert "최적 추천" not in app_source
    assert "가장 유리한 조합" not in app_source
    assert "최적 추천" not in adapter_source
    assert "가장 유리한 조합" not in adapter_source


if __name__ == "__main__":

    test_recommendation_demo_uses_service_layer()
    test_mock_adapter_contains_valid_and_rejected_combinations()
    test_service_can_select_api_adapter_without_removing_mock()
    test_demo_displays_null_amount_as_not_calculable()
    test_evidence_snippets_are_exposed_in_demo_detail()
    test_forbidden_best_recommendation_phrase_is_not_rendered()
    print("test_frontend_recommendation_demo passed")
