function display(value) { return value || "-"; }

export default function ResultsTable({ tenders, emptyMessage = "Aucun appel d'offres trouvé." }) {
  return (
    <div className="results-wrap">
      <p className="result-count">Nombre de résultats : <strong>{tenders.length}</strong></p>
      {!tenders.length && <p className="empty-state">{emptyMessage}</p>}
      {!!tenders.length && (
      <div className="table-scroll">
        <table>
          <thead><tr><th>Titre</th><th>Organisme</th><th>Publication</th><th>Deadline</th><th>Source</th><th>Méthode</th><th>Documents</th></tr></thead>
          <tbody>{tenders.map((tender) => (
            <tr key={tender.id}>
              <td><strong>{display(tender.title)}</strong>{tender.description && <small>{tender.description}</small>}</td>
              <td>{display(tender.owner)}</td>
              <td>{display(tender.published_date)}</td>
              <td>{display(tender.deadline)}</td>
              <td><a href={tender.source_url} target="_blank" rel="noreferrer">Ouvrir</a></td>
              <td><span className="method-badge">{display(tender.extraction_method)}</span></td>
              <td>{tender.documents?.length ? tender.documents.map((document, index) => <a className="document-link" key={document} href={document} target="_blank" rel="noreferrer">Document {index + 1}</a>) : "-"}</td>
            </tr>
          ))}</tbody>
        </table>
      </div>
      )}
    </div>
  );
}
