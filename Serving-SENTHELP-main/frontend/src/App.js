import React, { useState, useEffect, useRef } from "react";
import Select from "react-select";
import Sidebar from "./components/Sidebar"; // Composant de la barre latérale à gauche
import Navbar from "./components/Navbar"; // Composant de la barre de navigation en haut
import Cards from "./components/Cards"; // Composant pour les cartes de statistiques
import Charts from "./components/Charts"; // Composant pour les graphiques
import {Timeline, SatisfactionTimeline} from "./components/Timeline"; // Composant pour les séries temporelles
import { GoDownload } from  "react-icons/go";
import Wordcloud from "./components/wordcloud"; // Composant pour le nuage de mots
import TopTweet from "./components/toptweets"; // Composant pour les tabulations de tweets
import html2pdf from "html2pdf.js";

import {
  applications,
  lines,
  reasons,
  dateRanges,
} from "./utils/mockData";

const App = () => {
  const [selectedView, setSelectedView] = useState("sentiment"); // vue par défaut
  const [filters, setFilters] = useState({
    application: null,
    line: null,
    reason: null,
  });

  
  const [tweets, setTweets] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [mainKeywords, setMainKeywords] = useState([]);
  const [selectedKeyword, setSelectedKeyword] = useState(mainKeywords[0] || { value: "Aucun mot-clé", label: "Aucun mot-clé" });
  const [dateRange, setDateRange] = useState(dateRanges[0] || { value: null, label: "Toute la période" });

  useEffect(() => {
    localStorage.setItem("dashboardFilters", JSON.stringify(filters));
  }, [filters]);

useEffect(() => {
  let newFilteredData = tweets;

  // filtre par période
  if (dateRange && dateRange.value !== null) {
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - dateRange.value);

    newFilteredData = newFilteredData.filter((row) => {
      const tweetDate = new Date(row.date_tweet_cleaned);
      return !isNaN(tweetDate) && tweetDate >= startDate;
    });
  }

  // filtre par mot-clé principal
  if (selectedKeyword !== null && selectedKeyword.value !== "Aucun mot-clé") {
    newFilteredData = newFilteredData.filter((row) =>
      row.mot_cle?.toLowerCase().includes(`"${selectedKeyword.value}"`)
    );
  }

  setFilteredData(newFilteredData);
}, [tweets, dateRange, selectedKeyword]);



  const fetchtweets = async () => {
    try {
      const response = await fetch("http://localhost:8000/tweets/");
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      const data = await response.json();
      setTweets(data.tweets);
      const keywords = extractMainKeywords(data.tweets);
      setMainKeywords(keywords);
    } catch (error) {
      console.error("Erreur fetch:", error);
    }
  };

  useEffect(() => {
    fetchtweets();
  }, []);
  

const pageRef = useRef();

const handleExport = () => {
  if (pageRef.current) {
    const element = pageRef.current;

    const opt = {
      margin:       0.5,
      filename:     "rapport.pdf",
      image:        { type: "jpeg", quality: 0.98 },
      html2canvas:  { scale: 2 },
      jsPDF:        { unit: "in", format: "a4", orientation: "portrait" },
    };

    html2pdf().set(opt).from(element).save();
  }
};

const extractMainKeywords = (tweets) => {
  const mainKeywordsSet = new Set();
  mainKeywordsSet.add("Aucun mot-clé");
  tweets.forEach((tweet) => {
    const raw = tweet.mot_cle;
    if (raw) {
      const match = raw.match(/"([^"]+)"/); // capture ce qui est entre guillemets
      if (match && match[1]) {
        mainKeywordsSet.add(match[1].toLowerCase());
      }
    }
  });

  return Array.from(mainKeywordsSet).map((keyword) => ({
    value: keyword,
    label: keyword,
  }));
};

  


  return (
    <div className="container">
      <Sidebar selectedView={selectedView} onViewChange={setSelectedView} />
      <div className="main-content">
        <Navbar />
        <div className="filters">
          <Select
            options={dateRanges}
            value={dateRange}
            placeholder="Sélectionner une période"
            onChange={(selected) => setDateRange(selected)}
          />
          <Select
            options={mainKeywords}
            value={selectedKeyword}
            placeholder="Sélectionner un mot-clé"
            onChange={setSelectedKeyword}
          />
          <button className="download-btn" onClick={handleExport}>
            <GoDownload className="icon" /> Télécharger le rapport PDF
          </button>
        </div>
        <div ref={pageRef}>
        <div className="charts">
        <p style={{ fontSize: "20px" }}>
            {filteredData.length > 0
            ? (() => {
            const dates = filteredData
              .map((tweet) => new Date(tweet.date_tweet_cleaned))
              .filter((d) => !isNaN(d)); // retire les dates invalides

            const minDate = new Date(Math.min(...dates));
            const maxDate = new Date(Math.max(...dates));

            const format = (d) => d.toLocaleDateString("fr-FR");

            return `Période d'analyse : ${format(minDate)} - ${format(maxDate)}`;
          })()
        : "Aucune donnée disponible"}
          </p>
        </div>


        {/* Vue conditionnelle */}
        {selectedView === "stats" ? (
          <>
            <TopTweet tweets={filteredData} />
          </>
        ) : (
          <>
          <div style={styles.section}><Cards filteredData={filteredData} /></div>
          <div style={styles.grid}>
            <div style={styles.leftColumn}>
              <div style={styles.section}><Charts tweets={filteredData} /></div>
              <div style={styles.section}><SatisfactionTimeline tweets={filteredData} option={dateRange} keyword={selectedKeyword} /></div>
            </div>
            <div style={styles.rightColumn}>
              <div style={styles.section}><Wordcloud tweets={filteredData} /></div>
            </div>
          </div>
          <Timeline tweets={filteredData} option={dateRange} keyword={selectedKeyword} />
          </>
        )}
      </div>
    </div>
    </div>

  );
};

export default App;
const styles = {
  grid: {
    display: "flex",
    flexWrap: "wrap",
    justifyContent: "space-between",
    gap: "20px",
    marginTop: "20px"
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
  section: {
    backgroundColor: "#ffffff",
    padding: "16px",
    borderRadius: "12px",
    boxShadow: "0 4px 10px rgba(0,0,0,0.05)"
  }
};
