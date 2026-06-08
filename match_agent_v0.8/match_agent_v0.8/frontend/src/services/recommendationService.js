import { fetchRecommendationDemo as fetchMockRecommendationDemo } from './mockRecommendationAdapter.js';

const recommendationAdapter = {
  fetchRecommendationDemo: fetchMockRecommendationDemo,
};

export function getRecommendationService() {
  return recommendationAdapter;
}

export async function fetchGeneralCompanyRecommendationDemo(input) {
  return recommendationAdapter.fetchRecommendationDemo(input);
}
