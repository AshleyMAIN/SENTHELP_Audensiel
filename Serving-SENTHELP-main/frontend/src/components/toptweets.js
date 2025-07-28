import React from "react";

const getTopTweetsBy = (tweets, key, limit = 10) => {
  return [...tweets]
    .sort((a, b) => (b[key] || 0) - (a[key] || 0))
    .slice(0, limit);
};

const TweetTable = ({ title, tweets }) => (
  <div className="table-container">
    <h3 className="table-title">{title}</h3>
    <table className="table-beautiful">
      <thead>
        <tr>
          <th>Texte</th>
          <th>Emotion</th>
          <th>Date</th>
          <th>Mot-clé</th>
          <th>❤️ Likes</th>
          <th>👁️ Vues</th>
          <th>💬 Com.</th>
          <th>🔁 RT</th>
        </tr>
      </thead>
      <tbody>
        {tweets.map((tweet, index) => (
            <tr key={index}>
              <td title={tweet.text_tweet}>{tweet.text_tweet}</td>
              <td>{tweet.emotion || "N/A"}</td>
              <td>{tweet.date_tweet_cleaned || "?"}</td>
              <td>{tweet.mot_cle || "-"}</td>
              <td>{tweet.nombre_likes || 0}</td>
              <td>{tweet.nombre_views || 0}</td>
              <td>{tweet.nombre_replies || 0}</td>
              <td>{tweet.nombre_reposts || 0}</td>
            </tr>
          ))}
      </tbody>
    </table>
  </div>
);

export const TopTweet = ({ tweets }) => {
  const topLikes = getTopTweetsBy(tweets, "nombre_likes");
  const topViews = getTopTweetsBy(tweets, "nombre_views");
  const topComments = getTopTweetsBy(tweets, "nombre_replies");
  const topRetweets = getTopTweetsBy(tweets, "nombre_reposts");

  return (
    <div style={{ padding: "2rem" }}>
      <h2 style={{ fontSize: "2rem", fontWeight: "bold", textAlign: "center", color: "#3730a3", marginBottom: "2rem" }}>
        🔝 Top Tweets par Indicateurs
      </h2>
      <TweetTable title="❤️ Top 10 Likes" tweets={topLikes} />
      <TweetTable title="👁️ Top 10 Vues" tweets={topViews} />
      <TweetTable title="💬 Top 10 Commentaires" tweets={topComments} />
      <TweetTable title="🔁 Top 10 Retweets" tweets={topRetweets} />
    </div>
  );
};

export default TopTweet;
