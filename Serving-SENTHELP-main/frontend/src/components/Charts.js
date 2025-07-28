import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
} from "recharts";
import {
  getSentimentPercentages,
  getNetSentimentScore,
  getCustomerSatisfactionScore,
  getPositiveNegativeRatio,
  getVolumeMentionsBySentiment,
  getEngagementRateBySentiment,
  getTopKeywordsBySentiment
} from './kpiFunctions';

const COLORS = {
  positif: "#3B82F6", // Bleu
  negatif: "#EF4444", // Rouge
};

const Charts = ({ tweets }) => {
  const sentiments = getSentimentPercentages(tweets);
  const mentions = getVolumeMentionsBySentiment(tweets);

  const totalTweets = tweets.length;

  const sentimentPieData = [
    { name: "Positif", value: sentiments.positive || 0, count: mentions.positive || 0 },
    { name: "Négatif", value: sentiments.negative || 0, count: mentions.negative || 0 },
  ];
  
 

  return (
    <div style={{
      display: "flex",
      flexWrap: "wrap",
      gap: "2rem",
      padding: "2rem",
      justifyContent: "center",
    }}>
      
      {/* Pie Chart */}
      <div style={{
        flex: "1 1 400px",
        backgroundColor: "#fff",
        borderRadius: "1rem",
        padding: "1.5rem",
        boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
      }}>
        <h3 style={{
          fontSize: "1.2rem",
          marginBottom: "1rem",
          color: "#111827",
          textAlign: "center",
        }}>
          Pourcentage de tweets par sentiments
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Legend verticalAlign="top" height={36} />
            <Pie
              data={sentimentPieData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={80}
              label={({ name, value, count }) =>
                `${name}: ${value}%`
              }
            >
              {sentimentPieData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={index === 0 ? COLORS.positif : COLORS.negatif}
                />
              ))}
            </Pie>
            <Tooltip 
                formatter={(value, name, props) => {
                  const count = props.payload.count;
                  return [`${value}% (${count} tweets)`, name];
                }} 
              />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};


export default Charts;
