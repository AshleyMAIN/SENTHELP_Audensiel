// composant pour les fonctions de calcul des KPI

// 1. Pourcentage de chaque sentiment
export function getSentimentPercentages(tweets) {
  const total = tweets.length;
  if (total === 0) return { positive: 0, negative: 0, neutral: 0 };

  const counts = tweets.reduce(
    (acc, t) => {
      if (t.emotion === "Positive") acc.positive++;
      else acc.negative++;
      return acc;
    },
    { positive: 0, negative: 0}
  );

  return {
    positive: (counts.positive / total) * 100,
    negative: (counts.negative / total) * 100
  };
}

// 2. Net Sentiment Score
export function getNetSentimentScore(tweets) {
  const { positive, negative } = getSentimentPercentages(tweets);
  return positive - negative;
}

// 3. Customer Satisfaction Score (pourcentage tweets positifs)
export function getCustomerSatisfactionScore(tweets) {
  const { positive } = getSentimentPercentages(tweets);
  return positive;
}

// 4. Positive-Negative Ratio
export function getPositiveNegativeRatio(tweets) {
  const counts = tweets.reduce(
    (acc, t) => {
      if (t.emotion === "Positive") acc.pos++;
      else  acc.neg++;
      return acc;
    },
    { pos: 0, neg: 0 }
  );
  if (counts.neg === 0) return counts.pos === 0 ? 0 : Infinity;
  return counts.pos / counts.neg;
}

// 5. Volume de mentions par sentiment
export function getVolumeMentionsBySentiment(tweets) {
  const counts = tweets.reduce(
    (acc, t) => {
      if (t.emotion === "Positive") acc.positive++;
      else  acc.negative++;
      return acc;
    },
    { positive: 0, negative: 0 }
  );
  return counts;
}

// 6. Engagement rate par sentiment
export function getEngagementRateBySentiment(tweets) {
  const engagement = tweets.reduce(
    (acc, t) => {
      const totalEngagement = (t.nombre_likes || 0) + (t.nombre_reposts || 0) + (t.nombre_views || 0) + (t.nombre_replies || 0);
      if (t.emotion === "Positive") {
        acc.positive.totalEngagement += totalEngagement;
        acc.positive.count++;
      } else if (t.emotion === "Negative") {
        acc.negative.totalEngagement += totalEngagement;
        acc.negative.count++;
      }
      return acc;
    },
    {
      positive: { totalEngagement: 0, count: 0 },
      negative: { totalEngagement: 0, count: 0 },
    }
  );

  return {
    positive: engagement.positive.count === 0
      ? 0
      : (engagement.positive.totalEngagement / engagement.positive.count ) * 100,
    negative: engagement.negative.count === 0
      ? 0
      : (engagement.negative.totalEngagement / engagement.negative.count) * 100,
  };
}

// 7. Principaux thèmes (mots clés) par sentiment
export function getTopKeywordsBySentiment(tweets, topN = 5) {

  // Fonction pour extraire les mots-clés d'une liste de tweets
  const extractKeywords = (list, topN = 10) => {
  const keywordCounts = list.reduce((acc, tweet) => {
    const keyword = tweet.mot_cle;
    if (keyword) {
      const word = keyword.toLowerCase();
      acc[word] = (acc[word] || 0) + 1;
    }
    return acc;
  }, {});

  // Trier les mots-clés par fréquence décroissante
  const sorted = Object.entries(keywordCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, topN)
    .map(([word, count]) => ({ word, count }));

  return sorted;
};


  const posTweets = tweets.filter(t => t.emotion === 'Positive');
  const negTweets = tweets.filter(t => t.emotion === 'Negative');

  return {
    positive: extractKeywords(posTweets),
    negative: extractKeywords(negTweets),
  };
}