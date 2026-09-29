import { useState } from "react";
import ScrapeForm from "../components/ScrapeForm";
import ResultsTable from "../components/ResultsTable";
import { createScrape, getScrapeJob, getTenders } from "../api/client";

const POLL_INTERVAL = 2000;
const POLL_TIMEOUT = 120000;

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [tenders, setTenders] = useState([]);
  const [hasCompletedScrape, setHasCompletedScrape] = useState(false);
  const [progress, setProgress] = useState(null);

  async function handleScrape(url) {
    setLoading(true); setError(""); setTenders([]); setHasCompletedScrape(false); setProgress(null); setStatus("Découverte du site...");
    try {
      const accepted = await createScrape(url);
      const startedAt = Date.now();
      let job;
      do {
        await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL));
        if (Date.now() - startedAt > POLL_TIMEOUT) throw new Error("Le scraping a dépassé le délai maximal.");
        job = await getScrapeJob(accepted.job_id);
        setStatus(`Étape : ${job.current_stage || job.status}`);
        setProgress(job);
      } while (!["done", "failed"].includes(job.status));
      if (job.status === "failed") throw new Error(job.error_message || "Le scraping a échoué.");
      const result = await getTenders(accepted.job_id);
      setTenders(result.items);
      setHasCompletedScrape(true);
      setStatus("Scraping terminé");
    } catch (scrapeError) {
      setError(scrapeError.message || "Une erreur est survenue.");
      setStatus("");
    } finally { setLoading(false); }
  }

  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">OliveSoft / intelligence appels d'offres</p>
        <h1>OliveSoft Tender Scraper</h1>
        <p className="intro">Téléchargez une page publique, extrayez ses opportunités et consultez les résultats normalisés.</p>
      </section>
      <section className="panel"><ScrapeForm onSubmit={handleScrape} loading={loading} />{status && <p className="status">{status}</p>}{progress && <div className="progress-grid"><span>Pages visitées <strong>{progress.pages_visited} / {progress.max_pages}</strong></span><span>Pages candidates <strong>{progress.tender_pages_found}</strong></span><span>Tenders extraits <strong>{progress.tenders_extracted}</strong></span></div>}{error && <p className="error" role="alert">{error}</p>}</section>
      <section className="results-section"><div className="section-heading"><p className="eyebrow">Sortie normalisée</p><h2>Résultats</h2></div><ResultsTable tenders={tenders} emptyMessage={hasCompletedScrape ? "Aucun appel d'offres trouvé sur cette page." : "Lancez un scraping pour afficher les résultats."} /></section>
    </main>
  );
}
