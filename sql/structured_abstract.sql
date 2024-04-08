SELECT COUNT(*)
FROM document
WHERE
(abstract like '%DISCUSSION:%' or abstract like '%CONCLUSION:%'  or abstract like '%CONCLUSIONS:%')
and
(abstract like '%INTRODUCTION:%' or abstract like '%BACKGROUND:%')
and
(abstract like '%METHOD:%' or abstract like '%METHODS:%')
and
(abstract like '%RESULT:%' or abstract like '%RESULTS:%')
and collection = 'PubMed';