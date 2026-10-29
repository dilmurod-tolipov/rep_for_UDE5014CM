-- Q4. "Is the collection actually working, and is the data trustworthy?"
--     Asked by: me, every day of the collection window; and by the marker checking the data target.
--
-- One row per day: runs, how many succeeded on the approved definition (at least 80% of requested
-- pages fetched and parsed), the page success rate, new observations, and how many records were
-- quarantined. The 95% success rate promised in the proposal is read off successful_runs / runs.
--
-- Parameters: :purpose

SELECT substr(r.started_at, 1, 10)                              AS day,
       r.purpose,
       COUNT(*)                                                 AS runs,
       SUM(CASE WHEN r.status = 'success' THEN 1 ELSE 0 END)     AS successful_runs,
       SUM(r.pages_requested)                                   AS pages_requested,
       SUM(r.pages_ok)                                          AS pages_ok,
       CASE WHEN SUM(r.pages_requested) = 0 THEN NULL
            ELSE ROUND(100.0 * SUM(r.pages_ok) / SUM(r.pages_requested), 1) END AS page_success_pct,
       SUM(r.observations_saved)                                AS observations_saved,
       SUM(r.records_rejected)                                  AS records_quarantined
FROM scrape_runs r
WHERE r.purpose = :purpose
GROUP BY day, r.purpose
ORDER BY day DESC;
