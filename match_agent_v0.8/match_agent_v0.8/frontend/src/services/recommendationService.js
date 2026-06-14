import { fetchRecommendationDemo as fetchMockRecommendationDemo } from './mockRecommendationAdapter.js';
import { fetchRecommendationDemo as fetchApiRecommendationDemo } from './apiRecommendationAdapter.js';

const adapterName = import.meta.env.VITE_RECOMMENDATION_ADAPTER || 'mock';
const activeFetchRecommendationDemo = adapterName === 'api'
  ? fetchApiRecommendationDemo
  : fetchMockRecommendationDemo;

const recommendationAdapter = {
  name: adapterName === 'api' ? 'api' : 'mock',
  fetchRecommendationDemo: activeFetchRecommendationDemo,
};

export function getRecommendationService() {
  return recommendationAdapter;
}

export async function fetchGeneralCompanyRecommendationDemo(input) {
  return recommendationAdapter.fetchRecommendationDemo(input);
}
