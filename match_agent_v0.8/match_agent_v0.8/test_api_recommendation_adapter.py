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


def test_api_adapter_posts_to_demo_recommendation_endpoint():

    adapter_source = read_frontend_file(
        "services/apiRecommendationAdapter.js"
    )

    assert "/api/demo/recommendations/calculate" in adapter_source
    assert "method: 'POST'" in adapter_source
    assert "JSON.stringify(toApiRequest(input))" in adapter_source
    assert "policy_source" in adapter_source
    assert "VITE_RECOMMENDATION_POLICY_SOURCE" in adapter_source


def test_api_adapter_maps_required_response_fields():

    adapter_source = read_frontend_file(
        "services/apiRecommendationAdapter.js"
    )

    assert "recommended_combination" in adapter_source
    assert "alternative_combinations" in adapter_source
    assert "rejected_combinations" in adapter_source
    assert "errors" in adapter_source
    assert "meta" in adapter_source
    assert "summarized_combinations" in adapter_source


def test_recommendation_service_defaults_to_mock_adapter():

    service_source = read_frontend_file(
        "services/recommendationService.js"
    )

    assert "VITE_RECOMMENDATION_ADAPTER || 'mock'" in service_source
    assert "fetchMockRecommendationDemo" in service_source
    assert "fetchApiRecommendationDemo" in service_source


def test_demo_screen_displays_source_notice_and_recommended_card():

    app_source = read_frontend_file(
        "App.jsx"
    )

    assert "데모 정책 데이터 기준 결과입니다." in app_source
    assert "Supabase 테스트 정책 DB 기준 결과입니다." in app_source
    assert "recommended_combination" in app_source
    assert "추천 조합" in app_source


def test_mock_adapter_still_exists():

    adapter_source = read_frontend_file(
        "services/mockRecommendationAdapter.js"
    )

    assert "fetchRecommendationDemo" in adapter_source
    assert "isMock: true" in adapter_source


if __name__ == "__main__":

    test_api_adapter_posts_to_demo_recommendation_endpoint()
    test_api_adapter_maps_required_response_fields()
    test_recommendation_service_defaults_to_mock_adapter()
    test_demo_screen_displays_source_notice_and_recommended_card()
    test_mock_adapter_still_exists()
    print("test_api_recommendation_adapter passed")
