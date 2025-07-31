import React, { useMemo, useRef, useState, useEffect } from "react";
import {
  getSentimentPercentages,
  getNetSentimentScore,
  getCustomerSatisfactionScore,
  getPositiveNegativeRatio,
  getVolumeMentionsBySentiment,
  getEngagementRateBySentiment,
  getTopKeywordsBySentiment
} from './kpiFunctions'; // fichier où tu as défini les fonctions
import {
  LineChart,
  ReferenceArea,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Brush,
} from "recharts";
import 'tippy.js/dist/tippy.css';
import 'tippy.js/animations/scale.css';


const Timeline = ({ tweets, option, keyword }) => {
  const tab_pourcentage_sentiment = [];

  const groupedTweets = tweets.reduce((acc, tweet) => {
  const date = new Date(tweet.date_tweet_cleaned).toISOString().split("T")[0];
  if (!acc[date]) acc[date] = [];
  acc[date].push(tweet);
  return acc;
}, {});

// Récupérer les dates triées
const sortedDates = Object.keys(groupedTweets).sort((a, b) => new Date(a) - new Date(b));

  for (const date of sortedDates) {
    const dailyTweets = groupedTweets[date];
    const sentiments = getSentimentPercentages(dailyTweets);
    const volumeMentions = getVolumeMentionsBySentiment(dailyTweets);
    tab_pourcentage_sentiment.push({
      date,
      positive: sentiments.positive,
      negative: sentiments.negative,
      countPositive: volumeMentions.positive || 0,
      countNegative: volumeMentions.negative || 0,
    });
  }

  // Zoom logic
  const zoomedDataRef = useRef([]);
  const [dateRange, setDateRange] = useState({ start: "", end: "" });

  const [isSelecting, setIsSelecting] = useState(false);
  const [selectionStart, setSelectionStart] = useState(null);
  const [selectionEnd, setSelectionEnd] = useState(null);

  // Spacing
  let n = 1;
  let filteredData = tab_pourcentage_sentiment;

  if (option?.label === "Last 3 Months") n = 7;
  if ((option?.label === "Last 6 Months")  && filteredData.length >= 60) n = 15;
  if (option?.label === "Last 6 Months") n = 14;
  if ((option?.label === "Last 6 Months")  && filteredData.length >= 60) n = 30;
  if ((option?.label === "Last Year")) n = 14;
  if ((option?.label === "Toute la période")) n = 14;
  if ((option?.label === "Last Year") && filteredData.length >= 60) n = 30;
  if ((option?.label === "Toute la période")  && filteredData.length >= 60) n = 50;

  if ((option?.label === "Last 6 Months" || option?.label === "Last Year" || option?.label === "Toute la période") && filteredData.length >= 60 ) {
    filteredData = filteredData.filter((_, index) => index % n === 0);
  }
  


  // Filter zoomed data when range is selected
  useEffect(() => {
  if (dateRange.start && dateRange.end) {
    const newData = tab_pourcentage_sentiment
      .filter((item) => item.date >= dateRange.start && item.date <= dateRange.end)
      .sort((a, b) => a.date.localeCompare(b.date)); // 👈 Tri croissant
    console.log("DATES TRIÉES :", tab_pourcentage_sentiment.map((d) => d.date));
    zoomedDataRef.current = newData;
  } else {
    zoomedDataRef.current = [];
  }

  console.log("dateRange updated:", dateRange);
  console.log("Zoomed data updated:", zoomedDataRef.current);
  console.log("=nb tweets:", zoomedDataRef.current.length);
}, [dateRange, tab_pourcentage_sentiment]);

  const displayedData =
    zoomedDataRef.current.length > 0 ? zoomedDataRef.current : filteredData;

  return (
    <div style={styles.grid}>
      <div style={styles.leftColumn}>
        <div style={styles.section}>
          <h2>Pourcentage de tweets par sentiment</h2>

          <ResponsiveContainer width="100%" height={300}>
            <LineChart
              data={filteredData}
              onMouseDown={(e) => {
                if (e && e.activeLabel) {
                  setIsSelecting(true);
                  setSelectionStart(e.activeLabel);
                  setSelectionEnd(e.activeLabel);
                }
              }}
              onMouseMove={(e) => {
                if (isSelecting && e && e.activeLabel) {
                  setSelectionEnd(e.activeLabel);
                }
              }}
              onMouseUp={() => {
                if (selectionStart && selectionEnd) {
                  const start =
                    selectionStart < selectionEnd
                      ? selectionStart
                      : selectionEnd;
                  const end =
                    selectionStart > selectionEnd
                      ? selectionStart
                      : selectionEnd;
                  setDateRange({ start, end });
                }
                setIsSelecting(false);
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                interval={n}
                angle={-45}
                textAnchor="end"
              />
              <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
              <Tooltip
                formatter={(value, name, props) => {
                  let count = 0;
                  if (name === "Positif") count = props.payload.countPositive;
                  else if (name === "Négatif")
                    count = props.payload.countNegative;
                  return [`${value}% (${count} tweets)`, name];
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="positive"
                stroke="#4CAF50"
                name="Positif"
              />
              <Line
                type="monotone"
                dataKey="negative"
                stroke="#F44336"
                name="Négatif"
              />
              {/* Highlight selected area */}
              {selectionStart && selectionEnd && (
                <ReferenceArea
                  x1={selectionStart}
                  x2={selectionEnd}
                  strokeOpacity={0.3}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Zoom detail */}
      {selectionStart && selectionEnd &&displayedData.length > 0 && (
        <div style={styles.rightColumn}>
          <div style={styles.section}>
            <h3>Détail de la période sélectionnée</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={displayedData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" interval={7} angle={-45} textAnchor="end" />
                <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="positive"
                  stroke="#4CAF50"
                  name="Positif"
                />
                <Line
                  type="monotone"
                  dataKey="negative"
                  stroke="#F44336"
                  name="Négatif"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};


const SatisfactionTimeline = ({ tweets, option, keyword }) => {
  const tab_pourcentage_sentiment = []
  const tab_net_sentiment = []
  const tab_customer_satisfaction = []
  const tab_positive_negative_ratio = []
  const timelineData = [];
  // on a les tweets qui sont fitrés selon une période de temps
  // les tweets filtrés sont regroupés par jour

  const groupedTweets = tweets.reduce((acc, tweet) => {
  const date = new Date(tweet.date_tweet_cleaned).toISOString().split("T")[0];
  if (!acc[date]) acc[date] = [];
  acc[date].push(tweet);
  return acc;
}, {});

// Récupérer les dates triées
const sortedDates = Object.keys(groupedTweets).sort((a, b) => new Date(a) - new Date(b));
  
  // on itère sur les tweets groupés par jour
  for (const date of sortedDates) {
    const dailyTweets = groupedTweets[date];
    // on calcule les KPIs pour chaque jour
    const sentiments = getSentimentPercentages(dailyTweets);
    const netSentiment = getNetSentimentScore(dailyTweets);
    const satisfaction = getCustomerSatisfactionScore(dailyTweets);
    const ratio = getPositiveNegativeRatio(dailyTweets);
        // on ajoute les résultats dans les tableaux
    tab_pourcentage_sentiment.push({ date, ...sentiments });
    tab_net_sentiment.push({ date, netSentiment });
    tab_customer_satisfaction.push({ date, satisfaction });
    tab_positive_negative_ratio.push({ date, ratio });

    timelineData.push({
    date,
    positive: sentiments.positive,
    negative: sentiments.negative,
    netSentiment,
    satisfaction,
    ratio,
  });
  }

  // Choix de l’espacement de l’axe des X (optionnel si utilisé plus tard dans un graphique)
  // Spacing
  let n = 1;
  let filteredData = timelineData;

  if (option?.label === "Last 3 Months") n = 7;
  if ((option?.label === "Last 6 Months")  && filteredData.length >= 60) n = 15;
  if (option?.label === "Last 6 Months") n = 14;
  if ((option?.label === "Last 6 Months")  && filteredData.length >= 60) n = 30;
  if ((option?.label === "Last Year")) n = 14;
  if ((option?.label === "Toute la période")) n = 14;
  if ((option?.label === "Last Year") && filteredData.length >= 60) n = 30;
  if ((option?.label === "Toute la période")  && filteredData.length >= 60) n = 50;

  
  if ((option?.label === "Last 6 Months" || option?.label === "Last Year" || option?.label === "Toute la période") && filteredData.length >= 60 ) {
  filteredData = timelineData.filter((_, index) => index % n === 0);
  filteredData = filteredData.sort((a, b) => a.date.localeCompare(b.date));
  }
  
  return (
    <div >
        <h2>Satisfaction Client</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={filteredData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" interval={n} angle={-45} textAnchor="end" />
            <YAxis yAxisId="left" orientation="left" />
            <Tooltip formatter={(value, name) => [`${value}`, name]} />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="satisfaction" stroke="#FF9800" name="Satisfaction Client" />
          </LineChart>
        </ResponsiveContainer>
      </div>  );
}

export  { Timeline, SatisfactionTimeline };

const styles = {
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)", // toujours 2 colonnes fixes
    gap: "24px",
    padding: "20px",
  },
  section: {
    backgroundColor: "#fff",
    padding: "20px",
    borderRadius: "12px",
    boxShadow: "0 4px 12px rgba(0,0,0,0.06)",
  },
  leftColumn: {
    flex: "1 1 45%", // s'adapte pour mobile
    display: "flex",
    flexDirection: "column",
    gap: "20px"
  },
  rightColumn: {
    flex: "1 1 45%",
    display: "flex",
    flexDirection: "column",
    gap: "20px"
  },
};

