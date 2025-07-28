import React from "react";
import { GrDocumentText } from "react-icons/gr";
import { TiTick } from "react-icons/ti";
import "../App.css";
import {
  getSentimentPercentages,
  getNetSentimentScore,
  getCustomerSatisfactionScore,
  getPositiveNegativeRatio
} from './kpiFunctions';

const Cards = ({ filteredData }) => {
  const netSentiment = getNetSentimentScore(filteredData);
  const satisfaction = getCustomerSatisfactionScore(filteredData);
  const ratio = getPositiveNegativeRatio(filteredData);

  return (
    <div style={styles.cardsContainer}>
      <Card
        title="Net Sentiment"
        value={netSentiment}
        icon={<TiTick style={{ fontSize: 30, color: "#4CAF50" }} />}
        bgColor="#E8F5E9"
      />
      <Card
        title="Client Satisfaction"
        value={satisfaction}
        icon={<GrDocumentText style={{ fontSize: 30, color: "#2196F3" }} />}
        bgColor="#E3F2FD"
      />
      <Card
        title="Sentiment Ratio"
        value={ratio}
        icon={<GrDocumentText style={{ fontSize: 30, color: "#FF9800" }} />}
        bgColor="#FFF3E0"
      />
    </div>
  );
};

const Card = ({ title, value, icon, bgColor }) => (
  <div style={{ ...styles.card, backgroundColor: bgColor }}>
    <div style={styles.iconContainer}>{icon}</div>
    <h5 style={styles.cardTitle}>{title}</h5>
    <p style={styles.cardValue}>{value}</p>
  </div>
);

const styles = {
  cardsContainer: {
    display: "flex",
    gap: "1.5rem",
    justifyContent: "center",
    flexWrap: "wrap",
    margin: "2rem 0"
  },
  card: {
    flex: "1 1 250px",
    padding: "1.5rem",
    borderRadius: "15px",
    boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
    textAlign: "center"
  },
  iconContainer: {
    marginBottom: "0.5rem"
  },
  cardTitle: {
    margin: "0.5rem 0",
    fontSize: "1.1rem",
    fontWeight: "600",
    color: "#333"
  },
  cardValue: {
    fontSize: "1.4rem",
    fontWeight: "bold",
    color: "#111"
  }
};

export default Cards;
