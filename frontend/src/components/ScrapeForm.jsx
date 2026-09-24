import { useState } from "react";

export default function ScrapeForm({ onSubmit, loading }) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    try {
      const parsed = new URL(url);
      if (!["http:", "https:"].includes(parsed.protocol)) throw new Error("Utilisez une URL HTTP ou HTTPS.");
      setError("");
      await onSubmit(url);
    } catch (submissionError) {
      setError(submissionError.message || "URL invalide.");
    }
  }

  return (
    <form className="scrape-form" onSubmit={handleSubmit}>
      <label htmlFor="site-url">URL du site</label>
      <div className="form-row">
        <input id="site-url" type="url" required value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://exemple.com" disabled={loading} />
        <button type="submit" disabled={loading}>{loading ? "SCRAPING..." : "SCRAPER"}</button>
      </div>
      {error && <p className="error" role="alert">{error}</p>}
    </form>
  );
}
