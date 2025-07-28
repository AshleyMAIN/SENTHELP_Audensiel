import React from "react";
import ReactWordcloud from "react-wordcloud";
import 'tippy.js/dist/tippy.css';
import 'tippy.js/animations/scale.css';

// Fonction pour nettoyer les keywords et compter les occurrences
const getKeywordFrequencies = (tweets, sentimentType) => {
  const frequencies = {};

  tweets.forEach((tweet) => {
    if (tweet.emotion === sentimentType && tweet.mot_cle) {
      // Nettoyer : séparer par 'and' ou 'or'
      const keywords = tweet.mot_cle
        .toLowerCase()
        .replace(/["()]/g, "")       // enlever guillemets et parenthèses
        .replace(/\band\b|\bor\b/g, "") // supprimer les opérateurs and, or
        .split(/\s+/)                // découper par espace
        .filter((word) => word.trim() !== "");
      
        
      // Ajouter chaque mot dans le dictionnaire
      const uniqueKeywords = [...new Set(keywords)]; // éviter double comptage par tweet
      uniqueKeywords.forEach((word) => {
        frequencies[word] = (frequencies[word] || 0) + 1;
      });
    }
  });

  return Object.entries(frequencies).map(([text, value]) => ({ text, value }));
};

const Wordcloud = ({ tweets }) => {
  const positiveWords = getKeywordFrequencies(tweets, "Positive");
  const negativeWords = getKeywordFrequencies(tweets, "Negative");

  const options = {
    rotations: 2,
    rotationAngles: [-90, 0],
    fontSizes: [20, 60],
  };

  return (
    <div>
      <h2>Top mots-clés Positifs</h2>
      <div className="chart-container" style={{ height: 345, width: "90%" }}>
        <ReactWordcloud words={positiveWords} options={options} />
      </div>

      <h2>Top mots-clés Négatifs</h2>
      <div className="chart-container" style={{ height: 345, width: "90%" }}>
        <ReactWordcloud words={negativeWords} options={options} />
      </div>
    </div>
  );
};

export default Wordcloud;
